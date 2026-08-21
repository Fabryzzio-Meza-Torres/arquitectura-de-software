const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
let token = sessionStorage.getItem('lease-demo-token') || ''

export function setToken(value) {
  token = value || ''
  if (token) sessionStorage.setItem('lease-demo-token', token)
  else sessionStorage.removeItem('lease-demo-token')
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function api(path, options = {}) {
  const { body, headers = {}, retryNetwork = false, ...rest } = options
  const requestHeaders = { ...headers }
  if (token) requestHeaders.Authorization = `Bearer ${token}`
  let payload = body
  if (body && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const attempts = retryNetwork ? 3 : 1
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(`${API_URL}${path}`, { ...rest, body: payload, headers: requestHeaders })
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }))
        const detail = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail)
        const httpError = new Error(detail || `HTTP ${response.status}`)
        httpError.isHttpError = true
        throw httpError
      }
      if (response.status === 204) return null
      return response.json()
    } catch (error) {
      if (attempt === attempts || error.isHttpError) throw error
      await wait(10_000)
    }
  }
}

export const sessionApi = {
  users: () => api('/api/demo/users'),
  select: (userId) => api('/api/demo/session', { method: 'POST', body: { user_id: userId } }),
}
