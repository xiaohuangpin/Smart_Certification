<template>
  <div class="excel-preview">
    <div v-if="loading" class="preview-center">
      <el-skeleton :rows="8" animated />
    </div>

    <el-result v-else-if="error" icon="warning" title="无法加载原始表格" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="load">重试</el-button>
      </template>
    </el-result>

    <template v-else>
      <el-tabs v-model="current" class="preview-tabs" type="card">
        <el-tab-pane v-for="sheet in sheets" :key="sheet.name" :name="sheet.name">
          <template #label>
            <span class="tab-label">
              {{ sheet.name }}
              <el-tag v-if="sheet.hidden" size="small" type="info" effect="plain">隐藏</el-tag>
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>

      <div ref="bodyRef" class="preview-body">
        <table class="preview-table" aria-label="Excel 原始表格预览">
          <thead>
            <tr>
              <th class="row-index">行</th>
              <th v-for="col in columnCount" :key="col">{{ colLetter(col - 1) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in currentSheet.rows"
              :id="`row-${i + 1}`"
              :key="i"
              :class="{ 'is-source': isSourceRow(i + 1) }"
            >
              <td class="row-index">{{ i + 1 }}</td>
              <td
                v-for="col in columnCount"
                :key="col"
                :class="{ 'is-amount': isAmountCell(i + 1, row[col - 1]) }"
              >
                {{ formatCell(row[col - 1]) }}
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!currentSheet.rows.length" class="cell-muted preview-empty">该工作表无数据</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import * as XLSX from 'xlsx'

interface SourcePoint {
  sheet: string
  row: number
  amount: string
}

interface SheetData {
  name: string
  hidden: boolean
  rows: unknown[][]
}

const props = defineProps<{
  url: string
  sources: SourcePoint[]
  activeSheet?: string
  activeRow?: number
}>()

const loading = ref(true)
const error = ref('')
const sheets = ref<SheetData[]>([])
const current = ref('')
const bodyRef = ref<HTMLElement | null>(null)

const currentSheet = computed<SheetData>(
  () => sheets.value.find((item) => item.name === current.value) ?? { name: '', hidden: false, rows: [] },
)
const columnCount = computed(() =>
  currentSheet.value.rows.reduce((max, row) => Math.max(max, row.length), 0),
)

const sourceRows = computed(() => {
  const map = new Map<number, string[]>()
  for (const point of props.sources) {
    if (point.sheet !== current.value) continue
    const amounts = map.get(point.row) ?? []
    amounts.push(point.amount)
    map.set(point.row, amounts)
  }
  return map
})

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch(props.url)
    if (!response.ok) throw new Error(`请求失败（${response.status}）`)
    sheets.value = parseSheets(await response.arrayBuffer())
    current.value =
      sheets.value.find((item) => item.name === props.activeSheet)?.name ??
      sheets.value[0]?.name ??
      ''
    await nextTick()
    scrollToActive()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '源文件加载失败，请重试'
  } finally {
    loading.value = false
  }
}

function parseSheets(data: ArrayBuffer): SheetData[] {
  const workbook = XLSX.read(data, { type: 'array' })
  const hiddenByName = new Map<string, boolean>()
  const workbookSheets = (workbook as XLSX.WorkBook & {
    Workbook?: { Sheets?: Array<{ name: string; Hidden?: number }> }
  }).Workbook?.Sheets
  for (const def of workbookSheets ?? []) {
    hiddenByName.set(def.name, (def.Hidden ?? 0) > 0)
  }
  return workbook.SheetNames.map((name) => ({
    name,
    hidden: hiddenByName.get(name) ?? false,
    rows: XLSX.utils.sheet_to_json(workbook.Sheets[name], {
      header: 1,
      raw: false,
      defval: '',
    }) as unknown[][],
  }))
}

function isSourceRow(excelRow: number): boolean {
  return sourceRows.value.has(excelRow)
}

function isAmountCell(excelRow: number, cell: unknown): boolean {
  const amounts = sourceRows.value.get(excelRow)
  return Boolean(amounts) && (amounts as string[]).some((amount) => cellMatches(cell, amount))
}

function cellMatches(cell: unknown, amount: string): boolean {
  const target = Number(amount)
  if (!Number.isNaN(target)) {
    const value = Number(cell)
    if (!Number.isNaN(value)) return Math.abs(value - target) < 1e-9
  }
  return formatCell(cell) === amount.trim()
}

function formatCell(cell: unknown): string {
  return cell === null || cell === undefined ? '' : String(cell)
}

function colLetter(index: number): string {
  let n = index + 1
  let result = ''
  while (n > 0) {
    const remainder = (n - 1) % 26
    result = String.fromCharCode(65 + remainder) + result
    n = Math.floor((n - 1) / 26)
  }
  return result
}

function scrollToActive() {
  if (!props.activeRow) return
  const element = bodyRef.value?.querySelector(`#row-${props.activeRow}`)
  element?.scrollIntoView({ block: 'center' })
}
</script>

<style scoped>
.preview-center {
  padding: 16px 0;
}

.preview-tabs :deep(.el-tabs__nav) {
  flex-wrap: wrap;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.preview-body {
  max-height: calc(100vh - 260px);
  overflow: auto;
  border: 1px solid var(--sc-border);
  border-radius: 8px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th,
.preview-table td {
  padding: 6px 10px;
  border-right: 1px solid var(--sc-border);
  border-bottom: 1px solid var(--sc-border);
  white-space: nowrap;
  text-align: left;
}

.preview-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f5f7fa;
  font-weight: 600;
}

.preview-table .row-index {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #f5f7fa;
  color: var(--sc-text-muted);
  text-align: center;
  min-width: 48px;
  font-variant-numeric: tabular-nums;
}

.preview-table tbody tr.is-source td {
  background: #fff7e6;
}

.preview-table td.is-amount {
  background: #fff1f0;
  color: #e2504c;
  font-weight: 700;
}

.preview-empty {
  padding: 24px;
  text-align: center;
}
</style>