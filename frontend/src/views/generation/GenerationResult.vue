<template>
  <div>
    <div class="page-head">
      <div>
        <h1>制证结果</h1>
        <p class="page-desc">核对 AI 生成的分录，确认无误后采纳；采纳后不可修改。</p>
      </div>
      <el-button aria-label="返回智能制证" @click="router.push('/generation')">返回制证</el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />

    <el-result
      v-else-if="loadError"
      icon="warning"
      title="无法加载制证结果"
      :sub-title="loadError"
    >
      <template #extra>
        <el-button type="primary" @click="refresh()">重新加载</el-button>
        <el-button @click="router.push('/generation')">返回制证</el-button>
      </template>
    </el-result>

    <el-card v-else-if="isRunning" shadow="never" class="page-card">
      <div class="running" role="status" aria-live="polite">
        <el-progress :percentage="100" :indeterminate="true" :duration="2" :show-text="false" />
        <p class="running-title">AI 正在读取 Excel 并生成凭证…</p>
        <p class="form-hint">
          任务在后台执行，通常需要几十秒。完成后会自动展示结果，请勿关闭页面。
        </p>
      </div>
    </el-card>

    <el-result
      v-else-if="task?.status === 'failed'"
      icon="error"
      title="生成失败"
      :sub-title="failureText"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/generation')">重新发起</el-button>
        <el-button @click="refresh()">刷新状态</el-button>
      </template>
    </el-result>

    <template v-else-if="voucher">
      <el-alert
        v-if="voucher.voucher_status === 'adopted'"
        type="success"
        title="该凭证已采纳，内容只读"
        :closable="false"
        show-icon
        class="block-alert"
      />
      <el-alert
        v-else-if="voucher.voucher_status === 'discarded'"
        type="info"
        title="该凭证已废弃，不会保存为正式记录"
        :closable="false"
        show-icon
        class="block-alert"
      />
      <el-alert
        v-else-if="unbalanced"
        type="error"
        title="借贷不平衡"
        :description="`借方合计 ${voucher.debit_total ?? '—'}，贷方合计 ${voucher.credit_total ?? '—'}，差额 ${voucher.difference ?? '—'}。请重新生成，或检查模板的金额来源。`"
        :closable="false"
        show-icon
        class="block-alert"
      />
      <el-alert
        v-for="(item, index) in validations"
        :key="index"
        :type="item.level === 'error' ? 'error' : 'warning'"
        :title="item.message"
        :closable="false"
        show-icon
        class="block-alert"
      />

      <el-card shadow="never" class="page-card">
        <div class="voucher-header">
          <div>
            <div class="voucher-title">
              {{ voucher.summary || '生成的凭证' }}
              <el-tag :type="statusTag.type" effect="plain" size="small">{{ statusTag.text }}</el-tag>
            </div>
            <div class="form-hint">
              凭证号 {{ voucher.voucher_no || '—' }} · 模板 {{ task?.template_name }}（{{
                task?.template_code
              }}） · V{{ task?.template_version }}
            </div>
          </div>
          <el-button v-if="task?.source" @click="openPreview()">查看原始表格</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="page-card">
        <div class="card-title">分录明细</div>
        <el-table :data="voucher.entries" row-key="seq" aria-label="生成的分录明细">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="source-detail">
                <p>
                  <span class="cell-muted">取数说明：</span>{{ row.source_detail?.reason || '—' }}
                </p>
                <ul v-if="row.source_detail?.details?.length">
                  <li v-for="(detail, index) in row.source_detail.details" :key="index">
                    {{ detail.sheet_name }} 第 {{ detail.row_index }} 行，金额 {{ detail.amount }}
                  </li>
                </ul>
                <p v-else class="cell-muted">未提供具体取数行</p>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="seq" label="#" width="56" />
          <el-table-column label="方向" width="72">
            <template #default="{ row }">
              <el-tag
                :type="row.direction === 'debit' ? 'primary' : 'warning'"
                effect="plain"
                size="small"
              >
                {{ row.direction === 'debit' ? '借' : '贷' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="会计科目" min-width="200">
            <template #default="{ row }">
              <div>{{ row.account_name }}</div>
              <div class="cell-muted">{{ row.account_code }}</div>
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="摘要" min-width="140" show-overflow-tooltip />
          <el-table-column label="取数来源" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <el-button v-if="row.source_text" link type="primary" @click="entryFocus(row)">
                {{ row.source_text }}
              </el-button>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column label="金额" width="140" align="right">
            <template #default="{ row }">{{ row.amount }}</template>
          </el-table-column>
        </el-table>

        <div class="totals">
          <div>
            <span>借方合计</span>
            <strong>{{ voucher.debit_total ?? '—' }}</strong>
          </div>
          <div>
            <span>贷方合计</span>
            <strong>{{ voucher.credit_total ?? '—' }}</strong>
          </div>
          <div :class="{ 'is-error': unbalanced }">
            <span>差额</span>
            <strong>{{ voucher.difference ?? '—' }}</strong>
          </div>
        </div>
      </el-card>

      <div class="editor-actions">
        <span
          v-if="voucher.voucher_status === 'pending' && !canAdopt"
          class="form-hint"
        >
          {{ adoptHint }}
        </span>
        <el-button
          type="danger"
          plain
          :disabled="!canDiscard"
          :loading="acting === 'discard'"
          @click="discard"
        >
          废弃凭证
        </el-button>
        <el-button
          type="primary"
          :disabled="!canAdopt"
          :loading="acting === 'adopt'"
          @click="adopt"
        >
          采纳凭证
        </el-button>
      </div>

      <el-drawer
        v-model="drawerVisible"
        size="65%"
        :title="task?.source?.filename || '原始表格'"
        :destroy-on-close="true"
      >
        <ExcelPreview
          v-if="task?.source"
          :url="task.source.url"
          :sources="sources"
          :active-sheet="focus?.sheet"
          :active-row="focus?.row"
        />
      </el-drawer>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generationApi } from '../../api'
import { HttpError, errorText } from '../../api/http'
import ExcelPreview from '../../components/ExcelPreview.vue'
import type { GeneratedEntry, GenerationTask } from '../../types'

interface SourcePoint {
  sheet: string
  row: number
  amount: string
}

const route = useRoute()
const router = useRouter()
const taskId = String(route.params.taskId ?? '')

const task = ref<GenerationTask | null>(null)
const loading = ref(true)
const loadError = ref('')
const acting = ref<'adopt' | 'discard' | null>(null)
const drawerVisible = ref(false)
const focus = ref<SourcePoint | null>(null)
let timer: number | undefined

const voucher = computed(() => task.value?.voucher ?? null)
const isRunning = computed(
  () => task.value?.status === 'pending' || task.value?.status === 'running',
)
const unbalanced = computed(() => Boolean(voucher.value && voucher.value.difference !== '0.00'))
const validations = computed(() => (unbalanced.value ? [] : (voucher.value?.validation ?? [])))
const sources = computed<SourcePoint[]>(() => {
  const filename = task.value?.source?.filename ?? ''
  const result: SourcePoint[] = []
  for (const entry of voucher.value?.entries ?? []) {
    for (const detail of entry.source_detail?.details ?? []) {
      result.push({
        sheet: stripFilename(detail.sheet_name, filename),
        row: detail.row_index,
        amount: detail.amount,
      })
    }
  }
  return result
})
const canAdopt = computed(
  () =>
    Boolean(voucher.value) &&
    voucher.value?.voucher_status === 'pending' &&
    !unbalanced.value &&
    !voucher.value?.validation.some((item) => item.level === 'error'),
)
const canDiscard = computed(() => voucher.value?.voucher_status === 'pending')
const adoptHint = computed(() =>
  unbalanced.value ? '借贷不平衡，无法采纳，请重新生成' : '存在校验错误，无法采纳，请重新生成',
)
const statusTag = computed(() => {
  switch (voucher.value?.voucher_status) {
    case 'adopted':
      return { type: 'success' as const, text: '已采纳' }
    case 'discarded':
      return { type: 'info' as const, text: '已废弃' }
    default:
      return { type: 'warning' as const, text: '待确认' }
  }
})
const failureText = computed(() => {
  const messages: Record<string, string> = {
    ENGINE_NOT_CONFIGURED: '智能制证引擎尚未接入，请联系管理员配置模型后再试。',
    EXCEL_PARSE_ERROR: 'Excel 读取失败，请确认文件未加密、为 .xlsx 格式后重新提交。',
    INVALID_ENGINE_RESULT: 'AI 返回的结果无法解析，请重新发起制证。',
    GENERATION_FAILED: '生成过程中出现异常，请重新发起；若持续失败请联系管理员。',
  }
  return (
    messages[task.value?.error_code ?? ''] ||
    task.value?.error_message ||
    '生成失败，请重新发起。'
  )
})

onMounted(refresh)
onUnmounted(stopPolling)

async function refresh(silent = false) {
  if (!silent) loading.value = true
  try {
    task.value = await generationApi.detail(taskId)
    loadError.value = ''
    if (isRunning.value) startPolling()
    else stopPolling()
  } catch (error) {
    if (silent) stopPolling()
    else loadError.value = errorText(error, '无法加载制证结果，请稍后重试')
  } finally {
    if (!silent) loading.value = false
  }
}

function startPolling() {
  if (timer) return
  timer = window.setInterval(() => refresh(true), 1500)
}

function stopPolling() {
  if (timer) {
    window.clearInterval(timer)
    timer = undefined
  }
}

function stripFilename(raw: string, filename: string): string {
  const prefix = `${filename}-`
  return raw.startsWith(prefix) ? raw.slice(prefix.length) : raw
}

function openPreview(point?: SourcePoint) {
  focus.value = point ?? null
  drawerVisible.value = true
}

function entryFocus(entry: GeneratedEntry) {
  const detail = entry.source_detail?.details?.[0]
  if (!detail) return
  openPreview({
    sheet: stripFilename(detail.sheet_name, task.value?.source?.filename ?? ''),
    row: detail.row_index,
    amount: detail.amount,
  })
}

async function adopt() {
  if (!canAdopt.value) return
  try {
    await ElMessageBox.confirm(
      '采纳后凭证将保存为正式记录，且不可再次修改。确认采纳吗？',
      '采纳凭证',
      { type: 'info', confirmButtonText: '确认采纳', cancelButtonText: '再检查一下' },
    )
  } catch {
    return
  }
  acting.value = 'adopt'
  try {
    task.value = await generationApi.adopt(taskId)
    ElMessage.success('凭证已采纳')
  } catch (error) {
    ElMessage.error(actionError(error))
  } finally {
    acting.value = null
  }
}

async function discard() {
  if (!canDiscard.value) return
  try {
    await ElMessageBox.confirm(
      '废弃后本次生成结果将不再使用，且不可恢复。确认废弃吗？',
      '废弃凭证',
      { type: 'warning', confirmButtonText: '确认废弃', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  acting.value = 'discard'
  try {
    task.value = await generationApi.discard(taskId)
    ElMessage.success('凭证已废弃')
  } catch (error) {
    ElMessage.error(actionError(error))
  } finally {
    acting.value = null
  }
}

function actionError(error: unknown) {
  if (error instanceof HttpError) {
    const messages: Record<string, string> = {
      VOUCHER_UNBALANCED: '借贷不平衡，暂不能采纳。请重新生成后再试。',
      VOUCHER_ALREADY_ADOPTED: '该凭证已采纳，无需重复操作。',
      VOUCHER_DISCARDED: '该凭证已废弃，不能再采纳。',
      TASK_NOT_READY: '任务尚未完成，请稍候再试。',
    }
    if (messages[error.code]) return messages[error.code]
  }
  return errorText(error)
}
</script>

<style scoped>
.running {
  padding: 32px 8px;
  text-align: center;
}

.running-title {
  margin: 20px 0 4px;
  font-size: 15px;
  font-weight: 600;
}

.block-alert {
  margin-bottom: 12px;
}

.voucher-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.voucher-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.totals {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 32px;
  margin-top: 16px;
  padding: 14px 8px;
  border-top: 1px solid var(--sc-border);
}

.totals div {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: var(--sc-text-muted);
  font-size: 12px;
}

.totals strong {
  color: var(--sc-text);
  font-size: 16px;
  font-variant-numeric: tabular-nums;
}

.totals .is-error strong {
  color: var(--el-color-danger);
}

.source-detail {
  padding: 8px 24px 12px;
  font-size: 13px;
  line-height: 1.7;
}

.source-detail ul {
  margin: 6px 0 0;
  padding-left: 20px;
}
</style>
