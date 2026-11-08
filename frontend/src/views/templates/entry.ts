import type { Direction } from '../../types'

export interface EntryErrors {
  direction?: string
  account_code?: string
}

export interface EntryRow {
  key: string
  direction: Direction | ''
  account_code: string
  account_name: string
  amount_source: string
  summary_template: string
  errors: EntryErrors
}

let rowSeq = 0

export function createEntryRow(): EntryRow {
  rowSeq += 1
  return {
    key: `row-${rowSeq}-${Date.now()}`,
    direction: '',
    account_code: '',
    account_name: '',
    amount_source: '',
    summary_template: '',
    errors: {},
  }
}

export function validateField(row: EntryRow, field: keyof EntryErrors): boolean {
  let message = ''
  if (field === 'direction') message = row.direction ? '' : '请选择方向'
  if (field === 'account_code') message = row.account_code ? '' : '请选择会计科目'
  row.errors[field] = message || undefined
  return !message
}

export function validateEntryRow(row: EntryRow): boolean {
  return (['direction', 'account_code'] as const).map((field) => validateField(row, field)).every(Boolean)
}
