const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

type RequestOptions = {
  method?: 'GET' | 'POST'
  params?: Record<string, string | number | boolean | undefined>
  body?: unknown
  timeoutMs?: number
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin)
  Object.entries(options.params ?? {}).forEach(([key, value]) => {
    if (value !== undefined) url.searchParams.set(key, String(value))
  })

  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs ?? 15000)

  try {
    const response = await fetch(url, {
      method: options.method ?? 'GET',
      headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })

    if (!response.ok) {
      let message = `Falha na API (${response.status})`
      try {
        const problem = await response.json()
        message = problem.detail ?? problem.title ?? message
      } catch {
        // Retain the HTTP status when the response body is not JSON.
      }
      throw new ApiError(message, response.status)
    }

    return await response.json() as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('A API demorou demais para responder.')
    }
    throw new ApiError('Não foi possível conectar à API. Verifique se ela está em execução.')
  } finally {
    window.clearTimeout(timeout)
  }
}