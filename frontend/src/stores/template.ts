import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { optionApi, templateApi } from '../api'
import { errorText } from '../api/http'
import type { EntityStatus, OptionData, TemplateSummary, TemplateWriteInput } from '../types'

export const useTemplateStore = defineStore('template', () => {
  const list = ref<TemplateSummary[]>([])
  const total = ref(0)
  const loading = ref(false)
  const initialized = ref(false)
  const filters = reactive<{
    keyword: string
    tag: string
    status: '' | EntityStatus
    page: number
    page_size: number
  }>({
    keyword: '',
    tag: '',
    status: '',
    page: 1,
    page_size: 20,
  })

  const options = ref<OptionData>({ scenarios: [], accounts: [] })
  const optionsLoaded = ref(false)

  async function fetchList() {
    loading.value = true
    try {
      const result = await templateApi.list({
        keyword: filters.keyword.trim() || undefined,
        tag: filters.tag.trim() || undefined,
        status: filters.status || undefined,
        page: filters.page,
        page_size: filters.page_size,
      })
      list.value = result.items
      total.value = result.total
    } catch (error) {
      list.value = []
      total.value = 0
      ElMessage.error(errorText(error, '模板列表加载失败，请重试'))
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  async function fetchOptions() {
    if (optionsLoaded.value) return options.value
    try {
      options.value = await optionApi.fetch()
      optionsLoaded.value = true
    } catch (error) {
      ElMessage.error(errorText(error, '基础选项加载失败，请刷新页面重试'))
    }
    return options.value
  }

  async function disable(id: string) {
    const updated = await templateApi.disable(id)
    const index = list.value.findIndex((item) => item.id === id)
    if (index >= 0) list.value[index] = { ...list.value[index], status: updated.status }
  }

  function remove(id: string) {
    return templateApi.remove(id)
  }

  function create(payload: TemplateWriteInput) {
    return templateApi.create(payload)
  }

  function update(id: string, payload: TemplateWriteInput) {
    return templateApi.update(id, payload)
  }

  function fetchDetail(id: string) {
    return templateApi.detail(id)
  }

  return {
    list,
    total,
    loading,
    initialized,
    filters,
    options,
    optionsLoaded,
    fetchList,
    fetchOptions,
    fetchDetail,
    create,
    update,
    disable,
    remove,
  }
})
