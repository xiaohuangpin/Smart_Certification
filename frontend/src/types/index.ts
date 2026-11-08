export type Direction = 'debit' | 'credit'
export type EntityStatus = 'enabled' | 'disabled'

export interface PageResult<T> {
  items: T[]
  total: number
}

export interface AccountSummary {
  id: string
  code: string
  name: string
  full_name: string
  status: EntityStatus
  created_at: string
  updated_at: string
}

export interface AccountCreateInput {
  code: string
  name: string
  full_name: string
  status: EntityStatus
}

export type AccountUpdateInput = Omit<AccountCreateInput, 'code'>

export interface OptionAccount {
  code: string
  name: string
  full_name: string
}

export interface OptionScenario {
  code: string
  name: string
}

export interface OptionData {
  scenarios: OptionScenario[]
  accounts: OptionAccount[]
}

export interface TemplateSummary {
  id: string
  code: string
  name: string
  scenario_code: string
  scenario_name: string
  tags: string[]
  version: number
  status: EntityStatus
  updated_at: string
}

export interface TemplateEntry {
  id: string
  seq: number
  direction: Direction
  account_code: string
  account_name: string
  amount_source: string
  summary_template: string
}

export interface TemplateDetail extends TemplateSummary {
  remark: string
  entries: TemplateEntry[]
  created_at: string
}

export interface TemplateEntryInput {
  direction: Direction
  account_code: string
  amount_source: string
  summary_template: string
}

export interface TemplateWriteInput {
  name: string
  scenario_code: string
  tags: string[]
  status: EntityStatus
  remark: string
  entries: TemplateEntryInput[]
}

export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed'
export type VoucherStatus = 'pending' | 'adopted' | 'discarded'

export interface VoucherValidation {
  level: 'error' | 'warning'
  message: string
}

export interface SourceRow {
  sheet_name: string
  row_index: number
  amount: string
}

export interface SourceDetail {
  reason?: string
  details?: SourceRow[]
}

export interface GeneratedEntry {
  seq: number
  direction: Direction
  account_code: string
  account_name: string
  summary: string
  amount: string
  aux: Record<string, string>
  source_text: string
  source_detail: SourceDetail
  confidence: number | null
}

export interface VoucherResult {
  voucher_no: string | null
  voucher_status: VoucherStatus
  summary: string
  debit_total: string | null
  credit_total: string | null
  difference: string | null
  validation: VoucherValidation[]
  entries: GeneratedEntry[]
}

export interface SourceFileInfo {
  filename: string
  size: number
  url: string
}

export interface GenerationTask {
  task_id: string
  status: TaskStatus
  template_code: string
  template_name: string
  template_version: number
  voucher: VoucherResult | null
  source: SourceFileInfo | null
  error_code: string | null
  error_message: string | null
}
