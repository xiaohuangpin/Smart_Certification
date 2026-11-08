<template>
  <div>
    <div class="card-title">
      <span>分录入 <span class="entry-count">共 {{ rows.length }} 行</span></span>
      <el-button type="primary" plain @click="addRow">新增分录</el-button>
    </div>
    <el-table :data="rows" row-key="key" class="entry-table" aria-label="模板分录列表">
      <el-table-column label="序号" width="60" align="center">
        <template #default="{ $index }">{{ $index + 1 }}</template>
      </el-table-column>
      <el-table-column label="方向" width="110">
        <template #default="{ row }">
          <div class="entry-cell" :class="{ 'is-error': row.errors.direction }">
            <el-select
              v-model="row.direction"
              placeholder="请选择"
              aria-label="分录方向"
              @change="row.errors.direction = undefined"
            >
              <el-option label="借" value="debit" />
              <el-option label="贷" value="credit" />
            </el-select>
            <div v-if="row.errors.direction" class="cell-error">{{ row.errors.direction }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="会计科目" min-width="250">
        <template #default="{ row }">
          <div class="entry-cell" :class="{ 'is-error': row.errors.account_code }">
            <AccountSelect
              :model-value="row.account_code"
              :account-name="row.account_name"
              @update:model-value="onAccountChange(row, $event)"
              @select="onAccountSelect(row, $event)"
            />
            <div v-if="row.errors.account_code" class="cell-error">{{ row.errors.account_code }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="金额来源与计算公式（选填）" min-width="230">
        <template #default="{ row }">
          <el-input
            v-model="row.amount_source"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 3 }"
            maxlength="500"
            placeholder="如：取税金计提表中代扣房产税额"
            aria-label="金额来源与计算公式（选填）"
          />
        </template>
      </el-table-column>
      <el-table-column label="摘要模板（选填）" min-width="200">
        <template #default="{ row }">
          <el-input
            v-model="row.summary_template"
            maxlength="200"
            placeholder="如：计提&#123;&#123;月份&#125;&#125;房产税"
            aria-label="摘要模板（选填）"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" align="center" fixed="right">
        <template #default="{ $index, row }">
          <el-button
            link
            type="danger"
            :disabled="rows.length === 1"
            :title="rows.length === 1 ? '至少保留一条分录' : '删除该分录'"
            :aria-label="`删除第 ${$index + 1} 条分录`"
            @click="removeRow($index)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <p class="form-hint">
      方向与会计科目为必填；金额来源、摘要模板选填。摘要模板支持 <span v-pre>{{月份}}</span> 等占位符。至少保留一条分录。
    </p>
  </div>
</template>

<script setup lang="ts">
import { nextTick } from 'vue'
import AccountSelect from '../../components/AccountSelect.vue'
import { createEntryRow, validateEntryRow, type EntryRow } from './entry'

const rows = defineModel<EntryRow[]>({ required: true })

type AccountOption = { code: string; name: string } | null

function addRow() {
  rows.value = [...rows.value, createEntryRow()]
}

function removeRow(index: number) {
  if (rows.value.length === 1) return
  rows.value = rows.value.filter((_, current) => current !== index)
}

function onAccountChange(row: EntryRow, code: string) {
  row.account_code = code
  row.errors.account_code = undefined
  if (!code) row.account_name = ''
}

function onAccountSelect(row: EntryRow, option: AccountOption) {
  row.account_name = option?.name ?? ''
}

async function validate() {
  const results = rows.value.map((row) => validateEntryRow(row))
  if (results.every(Boolean)) return true
  await nextTick()
  document.querySelector('.entry-cell.is-error')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  return false
}

defineExpose({ validate })
</script>

<style scoped>
.entry-count {
  color: var(--sc-text-muted);
  font-size: 13px;
  font-weight: 400;
  margin-left: 8px;
}

.entry-table {
  margin-top: 12px;
}
</style>
