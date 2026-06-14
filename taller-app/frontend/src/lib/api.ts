const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      const json = JSON.parse(text)
      if (typeof json.detail === 'string') {
        detail = json.detail
      } else if (Array.isArray(json.detail)) {
        // FastAPI validation errors: [{msg, loc, type}, ...]
        detail = json.detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ')
      }
    } catch {}
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export function apiGet<T>(path: string): Promise<T> {
  return fetch(`${API_BASE}${path}`).then(handleResponse<T>)
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  }).then(handleResponse<T>)
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(handleResponse<T>)
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(handleResponse<T>)
}

export function apiDelete(path: string): Promise<void> {
  return fetch(`${API_BASE}${path}`, { method: 'DELETE' }).then(handleResponse<void>)
}
