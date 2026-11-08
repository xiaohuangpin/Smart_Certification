<template>
  <div class="page">
    <div class="page-head">
      <div>
        <el-button link class="back-link" @click="goBack">← 返回模板列表</el-button>
        <h1>{{ isEdit ? '编辑凭证模板' : '新建凭证模板' }}</h1>
        <p class="page-desc">
          保存时整体校验基本信息与全部分录；至少需要一条分录，分录科目来自「会计科目」栏目。
        </p>
      </div>
    </div>

    <el-skeleton v-if="loading" class="page-card skeleton-card" :rows="8" animated />

    <el-card v-else-if="loadError" shadow="never" class="page-card">
      <el-empty :description="loadError">
        <div class="state-actions">
          <el-button @click="goBack">返回列表</el-button>
          <el-button type="primary" @click="load">重新加载</el-button>
        </div>
      </el-empty>
    </el-card>

    <template v-else>
      <el-card shadow="never" class="page-card">
        <div class="card-title">
          <span>基本信息</span>
          <span v-if="isEdit" class="version-hint">当前版本 V{{ detailVersion }}</span>
        </div>
        <el-form
          ref="basicRef"
          :model="form"
          :rules="basicRules"
          label-position="left"
          label-width="90px"
          class="basic-form"
          @submit.prevent
        >
          <div class="form-grid">
            <el-form-item label="模板编码">
              <el-input :model-value="detailCode || '保存后自动生成'" disabled aria-label="模板编码（只读）" />
            </el-form-item>
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="form.name" maxlength="50" placeholder="2–50 字" aria-label="模板名称" />
            </el-form-item>
            <el-form-item label="场景" prop="scenario_code">
              <el-select v-model="form.scenario_code" placeholder="请选择业务场景" filterable aria-label="业务场景">
                <el-option
                  v-for="scenario in store.options.scenarios"
                  :key="scenario.code"
                  :label="`${scenario.code} ${scenario.name}`"
                  :value="scenario.code"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="标签" prop="tags">
              <el-select
                v-model="form.tags"
                multiple
                filterable
                allow-create
                default-first-option
                collapse-tags
                collapse-tags-tooltip
                :multiple-limit="10"
                placeholder="输入后回车创建标签"
                aria-label="模板标签"
              >
                <el-option v-for="tag in form.tags" :key="tag" :label="tag" :value="tag" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" aria-label="模板状态">
                <el-option label="启用" value="enabled" />
                <el-option label="停用" value="disabled" />
              </el-select>
            </el-form-item>
            <el-form-item label="备注" prop="remark" class="form-span-all">
              <el-input
                v-model="form.remark"
                type="textarea"
                :rows="2"
                maxlength="255"
                show-word-limit
                placeholder="可选，用于说明模板用途"
                aria-label="模板备注"
              />
            </el-form-item>
          </div>
          <p class="form-hint">标签仅用于分类与检索，最多 10 个、单个不超过 20 字，不参与制证逻辑。</p>
        </el-form>
      </el-card>

      <el-card shadow="never" class="page-card entry-card">
        <EntryEditorTable ref="entryTable" v-model="entries" />
      </el-card>

      <div class="editor-actions">
        <el-button :disabled="saving" @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">
          {{ isEdit ? '保存修改' : '保存模板' }}
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import EntryEditorTable from './EntryEditorTable.vue'
import { createEntryRow, type EntryRow } from './entry'
import { HttpError, errorText } from '../../api/http'
import { useTemplateStore } from '../../stores/template'
import type { Direction, EntityStatus, TemplateDetail, TemplateWriteInput } from '../../types'

const route = useRoute()
const router = useRouter()
const store = useTemplateStore()

const isEdit = computed(() => Boolean(route.params.id))
const templateId = computed(() => String(route.params.id ?? ''))

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const dirty = ref(false)
const initializing = ref(true)
const detailCode = ref('')
const detailVersion = ref(1)

const basicRef = ref<FormInstance>()
const entryTable = ref<InstanceType<typeof EntryEditorTable>>()

const form = reactive<{
  name: string
  scenario_code: string
  tags: string[]
  status: EntityStatus
  remark: string
}>({
  name: '',
  scenario_code: '',
  tags: [],
  status: 'enabled',
  remark: '',
})

const entries = ref<EntryRow[]>([])

const validateTags = (_rule: unknown, value: string[], callback: (error?: Error) => void) => {
  if (value.length > 10) return callback(new Error('标签最多 10 个'))
  if (value.some((tag) => tag.length > 20)) return callback(new Error('单个标签最多 20 字'))
  callback()
}

const basicRules: FormRules = {
  name: [
    { required: true, message: '请填写模板名称', trigger: 'blur' },
    { min: 2, max: 50, message: '模板名称需为 2–50 字', trigger: 'blur' },
  ],
  scenario_code: [{ required: true, message: '请选择场景', trigger: 'change' }],
  tags: [{ validator: validateTags, trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}

watch(
  [form, entries],
  () => {
    if (!initializing.value) dirty.value = true
  },
  { deep: true },
)

function fillDetail(detail: TemplateDetail) {
  detailCode.value = detail.code
  detailVersion.value = detail.version
  form.name = detail.name
  form.scenario_code = detail.scenario_code
  form.tags = [...detail.tags]
  form.status = detail.status
  form.remark = detail.remark
  entries.value = detail.entries.map((entry) => {
    const row = createEntryRow()
    row.direction = entry.direction
    row.account_code = entry.account_code
    row.account_name = entry.account_name
    row.amount_source = entry.amount_source
    row.summary_template = entry.summary_template
    return row
  })
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    await store.fetchOptions()
    if (isEdit.value) {
      fillDetail(await store.fetchDetail(templateId.value))
    } else {
      entries.value = [createEntryRow()]
    }
    await nextTick()
    initializing.value = false
  } catch (error) {
    loadError.value = errorText(error, '模板加载失败，请返回列表后重试')
    initializing.value = false
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
  load()
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})

function onBeforeUnload(event: BeforeUnloadEvent) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm('当前修改尚未保存，离开后修改将丢失。', '未保存的修改', {
      type: 'warning',
      confirmButtonText: '离开',
      cancelButtonText: '继续编辑',
    })
    return true
  } catch {
    return false
  }
})

function goBack() {
  router.push('/templates')
}

async function save() {
  let basicValid = true
  try {
    await basicRef.value?.validate()
  } catch (fields) {
    basicValid = false
    const first = Object.keys((fields ?? {}) as Record<string, unknown>)[0]
    if (first) basicRef.value?.scrollToField(first)
  }
  if (!basicValid) {
    ElMessage.warning('请检查基本信息中标红的必填项')
    return
  }

  const entriesValid = await (entryTable.value?.validate() ?? Promise.resolve(false))
  if (!entriesValid) {
    ElMessage.warning('请检查分录中标红的必填项')
    return
  }

  const payload: TemplateWriteInput = {
    name: form.name.trim(),
    scenario_code: form.scenario_code,
    tags: form.tags.map((tag) => tag.trim()).filter(Boolean),
    status: form.status,
    remark: form.remark.trim(),
    entries: entries.value.map((row) => ({
      direction: row.direction as Direction,
      account_code: row.account_code,
      amount_source: row.amount_source.trim(),
      summary_template: row.summary_template.trim(),
    })),
  }

  saving.value = true
  try {
    if (isEdit.value) {
      const detail = await store.update(templateId.value, payload)
      ElMessage.success(`模板已保存，当前版本 V${detail.version}`)
    } else {
      const detail = await store.create(payload)
      ElMessage.success(`模板已创建：${detail.code}`)
    }
    dirty.value = false
    await router.push('/templates')
  } catch (error) {
    if (error instanceof HttpError) {
      const field = String(error.details?.field ?? '')
      const labels: Record<string, string> = {
        name: '模板名称',
        scenario_code: '场景',
        tags: '标签',
        remark: '备注',
        entries: '分录',
      }
      const prefix = labels[field] ? `「${labels[field]}」：` : ''
      const suggestion = error.message.includes('会计科目不可用')
        ? '。请到「会计科目」栏目启用该科目，或在分录中更换科目'
        : ''
      ElMessage.error(`${prefix}${error.message}${suggestion}`)
      if (field.startsWith('entries')) {
        document.querySelector('.entry-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    } else {
      ElMessage.error('保存失败，请稍后重试')
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.back-link {
  padding: 0;
  margin-bottom: 6px;
  font-size: 13px;
}

.skeleton-card {
  padding: 20px;
}

.state-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.basic-form {
  margin-top: 16px;
}

.basic-form :deep(.el-select) {
  width: 100%;
}

.version-hint {
  color: var(--sc-text-muted);
  font-size: 13px;
  font-weight: 400;
}

.entry-card {
  margin-top: 16px;
}
</style>
