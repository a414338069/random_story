export class FetchError extends Error {
  status: number
  code: string

  constructor(status: number, message: string, code: string) {
    super(message)
    this.name = 'FetchError'
    this.status = status
    this.code = code
  }
}

const TIMEOUT_MS = 10000

export async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!res.ok) {
      const body = await res.text()
      let detail = body
      try {
        const parsed = JSON.parse(body)
        detail = parsed.detail || parsed.message || body
      } catch { }
      throw new FetchError(res.status, String(detail), `HTTP_${res.status}`)
    }

    return await res.json()
  } catch (err) {
    if (err instanceof FetchError) throw err
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new FetchError(0, '连接超时，请检查网络', 'TIMEOUT')
    }
    throw new FetchError(0, '网络连接失败，请检查后端是否启动', 'NETWORK')
  } finally {
    clearTimeout(timeout)
  }
}
