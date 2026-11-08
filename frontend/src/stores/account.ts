import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi } from '../api'
import { errorText } from '../api/http'
import type { AccountCreateInput, AccountSummary, AccountUpdateInput, EntityStatus } from '../types'

export const useAccountStore = defineStore('account', () => {
  const list = ref<AccountSummary[]>([])
  const total = ref(0)
  const loading = ref(false)
  const initialized = ref(false)
  const filters = reactive<{ keyword: string; status: '' | EntityStatus; page: number; page_size: number }>({
    keyword: '',
    status: '',
    page: 1,
    page_size: 20,
  })

  async function fetchList() {
    loading.value = true
    try {
      const result = await accountApi.list({
        keyword: filters.keyword.trim() || undefined,
        status: filters.status || undefined,
        page: filters.page,
        page_size: filters.page_size,
      })
      list.value = result.items
      total.value = result.total
    } catch (error) {
      list.value = []
      total.value = 0
      ElMessage.error(errorText(error, '科目列表加载失败，请重试'))
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  function create(payload: AccountCreateInput) {
    return accountApi.create(payload)
  }

  function update(id: string, payload: AccountUpdateInput) {
    return accountApi.update(id, payload)
  }

  async function setStatus(id: string, enabled: boolean) {
    const updated = await accountApi.setStatus(id, enabled)
    const index = list.value.findIndex((item) => item.id === id)
    if (index >= 0) list.value[index] = updated
    return updated
  }

  function remove(id: string) {
    return accountApi.remove(id)
  }

  return { list, total, loading, initialized, filters, fetchList, create, update, setStatus, remove }
})
