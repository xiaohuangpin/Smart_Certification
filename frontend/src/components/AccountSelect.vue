<template>
  <el-select
    :model-value="modelValue"
    filterable
    clearable
    remote
    :remote-method="search"
    :loading="loading"
    :placeholder="placeholder"
    class="account-select"
    :aria-label="ariaLabel"
    @update:model-value="onChange"
    @visible-change="onVisibleChange"
  >
    <el-option
      v-for="option in options"
      :key="option.code"
      :label="`${option.code} ${option.name}`"
      :value="option.code"
    >
      <div class="account-option">
        <span class="account-option-code">{{ option.code }}</span>
        <span class="account-option-name">{{ option.name }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { accountApi } from '../api'
import { errorText } from '../api/http'
import { ElMessage } from 'element-plus'
import type { AccountSummary } from '../types'

interface SearchOption {
  code: string
  name: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string
    accountName?: string
    placeholder?: string
    ariaLabel?: string
  }>(),
  {
    accountName: '',
    placeholder: '搜索编码或名称',
    ariaLabel: '选择会计科目',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  select: [option: SearchOption | null]
}>()

const options = ref<SearchOption[]>([])
const loading = ref(false)
const loaded = ref(false)

const toOption = (account: AccountSummary): SearchOption => ({
  code: account.code,
  name: account.name,
})

function ensureSelected() {
  if (!props.modelValue) return
  if (options.value.some((item) => item.code === props.modelValue)) return
  options.value.unshift({
    code: props.modelValue,
    name: props.accountName || props.modelValue,
  })
}

async function search(keyword: string) {
  loading.value = true
  try {
    const result = await accountApi.list({ keyword: keyword.trim() || undefined, status: 'enabled', page: 1, page_size: 20 })
    options.value = result.items.map(toOption)
    loaded.value = true
    ensureSelected()
  } catch (error) {
    ElMessage.error(errorText(error, '科目搜索失败，请重试'))
  } finally {
    loading.value = false
  }
}

function onVisibleChange(visible: boolean) {
  if (visible && !loaded.value) search('')
}

function onChange(code: string) {
  emit('update:modelValue', code || '')
  emit('select', options.value.find((item) => item.code === code) ?? null)
}

watch(
  () => [props.modelValue, props.accountName] as const,
  () => ensureSelected(),
)

ensureSelected()
</script>

<style scoped>
.account-select {
  width: 100%;
}

.account-option {
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.account-option-code {
  color: var(--sc-text-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.account-option-name {
  font-size: 13px;
}
</style>
