import axios from 'axios'

interface ApiErrorBody {
  code: string
  message: string
  details?: Record<string, unknown>
}

export class HttpError extends Error {
  readonly code: string
  readonly details?: Record<string, unknown>
  readonly status?: number

  constructor(body: ApiErrorBody, status?: number) {
    super(body.message || '操作失败，请稍后重试')
    this.name = 'HttpError'
    this.code = body.code
    this.details = body.details
    this.status = status
  }
}

function errorText(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (error instanceof HttpError) return error.message
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export { errorText }

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

client.interceptors.response.use(
  (response) => response.data?.data,
  (error) => {
    const body: ApiErrorBody = error.response?.data?.error ?? {
      code: 'NETWORK_ERROR',
      message: error.response ? '服务暂时不可用，请稍后重试' : '无法连接服务，请确认后端已启动（127.0.0.1:5000）',
    }
    return Promise.reject(new HttpError(body, error.response?.status))
  },
)

type Params = Record<string, string | number | undefined>

export async function get<T>(url: string, params?: Params): Promise<T> {
  return (await client.get(url, { params })) as unknown as T
}

export async function post<T>(url: string, payload?: unknown): Promise<T> {
  return (await client.post(url, payload)) as unknown as T
}

export async function postForm<T>(url: string, form: FormData): Promise<T> {
  return (await client.post(url, form)) as unknown as T
}

export async function put<T>(url: string, payload?: unknown): Promise<T> {
  return (await client.put(url, payload)) as unknown as T
}

export async function del<T>(url: string): Promise<T> {
  return (await client.delete(url)) as unknown as T
}
