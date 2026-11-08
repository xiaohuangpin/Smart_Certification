<template>
  <div>
    <div class="page-head">
      <div>
        <h1>智能制证</h1>
        <p class="page-desc">
          选择凭证模板并上传业务 Excel，AI 会自动定位取数、计算金额并生成凭证草稿。
        </p>
      </div>
    </div>

    <el-card shadow="never" class="page-card form-card">
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="1. 选择凭证模板" required>
          <el-select
            v-model="templateId"
            class="full"
            placeholder="请选择要使用的凭证模板"
            :loading="templatesLoading"
            filterable
            aria-label="凭证模板"
          >
            <el-option
              v-for="item in templates"
              :key="item.id"
              :value="item.id"
              :label="`${item.name}（${item.code}）`"
            />
          </el-select>
          <div v-if="templatesLoading" class="form-hint">正在加载模板…</div>
          <div v-else-if="!templates.length" class="form-hint">
            暂无启用的模板，请先到
            <router-link to="/templates">凭证模板</router-link>
            创建并启用后再来制证。
          </div>
          <div v-else-if="selectedTemplate" class="form-hint">
            {{ selectedTemplate.scenario_name }} · 版本 V{{ selectedTemplate.version }}
          </div>
        </el-form-item>

        <el-form-item label="2. 上传业务 Excel" required>
          <el-upload
            class="full"
            drag
            accept=".xlsx,.xlsm"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="onFileChange"
          >
            <div class="upload-text">拖拽 Excel 到此处，或<em>点击选择文件</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .xlsx / .xlsm，单个文件不超过 20MB</div>
            </template>
          </el-upload>

          <div v-if="file" class="file-chip">
            <span class="file-name" :title="file.name">{{ file.name }}</span>
            <span class="cell-muted">{{ formatSize(file.size) }}</span>
            <el-button link type="danger" aria-label="移除已选择的 Excel" @click="file = null">
              移除
            </el-button>
          </div>
          <div v-if="fileError" class="cell-error" role="alert">{{ fileError }}</div>
        </el-form-item>
      </el-form>

      <div class="form-actions">
        <span class="form-hint">
          {{ canSubmit ? '提交后将在后台生成，通常需要几十秒' : '请先选择模板并上传 Excel' }}
        </span>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!canSubmit"
          aria-label="提交智能制证任务"
          @click="submit"
        >
          提交智能制证
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { generationApi, templateApi } from '../../api'
import { errorText } from '../../api/http'
import type { TemplateSummary } from '../../types'

const MAX_SIZE = 20 * 1024 * 1024
const router = useRouter()

const templates = ref<TemplateSummary[]>([])
const templatesLoading = ref(false)
const templateId = ref('')
const file = ref<File | null>(null)
const fileError = ref('')
const submitting = ref(false)

const selectedTemplate = computed(
  () => templates.value.find((item) => item.id === templateId.value) ?? null,
)
const canSubmit = computed(() => Boolean(templateId.value && file.value) && !submitting.value)

onMounted(loadTemplates)

async function loadTemplates() {
  templatesLoading.value = true
  try {
    const page = await templateApi.list({ status: 'enabled', page: 1, page_size: 100 })
    templates.value = page.items
  } catch (error) {
    ElMessage.error(errorText(error, '模板加载失败，请刷新页面重试'))
  } finally {
    templatesLoading.value = false
  }
}

function onFileChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  fileError.value = ''
  if (!raw) return
  const name = raw.name.toLowerCase()
  if (!name.endsWith('.xlsx') && !name.endsWith('.xlsm')) {
    fileError.value = '仅支持 .xlsx / .xlsm。请用 Excel 另存为工作簿后重新上传'
    file.value = null
    return
  }
  if (raw.size > MAX_SIZE) {
    fileError.value = `文件大小 ${formatSize(raw.size)}，超过 20MB，请精简工作表后重试`
    file.value = null
    return
  }
  file.value = raw
}

async function submit() {
  if (!canSubmit.value || !file.value) return
  submitting.value = true
  try {
    const task = await generationApi.create(templateId.value, file.value)
    ElMessage.success('已提交智能制证，正在生成凭证')
    router.push(`/generation/${task.task_id}`)
  } catch (error) {
    ElMessage.error(errorText(error, '提交失败，请检查网络后重试'))
  } finally {
    submitting.value = false
  }
}

function formatSize(size: number) {
  return size < 1024 * 1024
    ? `${Math.max(1, Math.ceil(size / 1024))} KB`
    : `${(size / 1024 / 1024).toFixed(1)} MB`
}
</script>

<style scoped>
.form-card {
  max-width: 760px;
}

.full {
  width: 100%;
}

.upload-text {
  color: var(--sc-text-muted);
  font-size: 14px;
  line-height: 1.6;
}

.upload-text em {
  color: var(--sc-primary);
  font-style: normal;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  padding: 8px 12px;
  border: 1px solid var(--sc-border);
  border-radius: 8px;
  background: #f8fafc;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.form-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 8px;
}
</style>
