import { del, get, post, postForm, put } from './http'
import type {
  AccountCreateInput,
  AccountSummary,
  AccountUpdateInput,
  GenerationTask,
  OptionData,
  PageResult,
  TemplateDetail,
  TemplateSummary,
  TemplateWriteInput,
} from '../types'

export const accountApi = {
  list(params: { keyword?: string; status?: string; page?: number; page_size?: number }) {
    return get<PageResult<AccountSummary>>('/accounts', params)
  },
  detail(id: string) {
    return get<AccountSummary>(`/accounts/${id}`)
  },
  create(payload: AccountCreateInput) {
    return post<AccountSummary>('/accounts', payload)
  },
  update(id: string, payload: AccountUpdateInput) {
    return put<AccountSummary>(`/accounts/${id}`, payload)
  },
  setStatus(id: string, enabled: boolean) {
    return post<AccountSummary>(`/accounts/${id}/${enabled ? 'enable' : 'disable'}`)
  },
  remove(id: string) {
    return del<null>(`/accounts/${id}`)
  },
}

export const templateApi = {
  list(params: { keyword?: string; tag?: string; status?: string; page?: number; page_size?: number }) {
    return get<PageResult<TemplateSummary>>('/templates', params)
  },
  detail(id: string) {
    return get<TemplateDetail>(`/templates/${id}`)
  },
  create(payload: TemplateWriteInput) {
    return post<TemplateDetail>('/templates', payload)
  },
  update(id: string, payload: TemplateWriteInput) {
    return put<TemplateDetail>(`/templates/${id}`, payload)
  },
  disable(id: string) {
    return post<TemplateSummary>(`/templates/${id}/disable`)
  },
  remove(id: string) {
    return del<null>(`/templates/${id}`)
  },
}

export const optionApi = {
  fetch() {
    return get<OptionData>('/options')
  },
}

export const generationApi = {
  create(templateId: string, file: File, context: Record<string, unknown> = {}) {
    const form = new FormData()
    form.append('template_id', templateId)
    form.append('context', JSON.stringify(context))
    form.append('file', file)
    return postForm<GenerationTask>('/smart-generation', form)
  },
  detail(taskId: string) {
    return get<GenerationTask>(`/smart-generation/${taskId}`)
  },
  adopt(taskId: string) {
    return post<GenerationTask>(`/smart-generation/${taskId}/adopt`)
  },
  discard(taskId: string) {
    return post<GenerationTask>(`/smart-generation/${taskId}/discard`)
  },
}
