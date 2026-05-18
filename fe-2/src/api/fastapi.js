import { API_BASE } from '../config'

/**
 * Bearer JWT auth — no cookies. Token comes from MSAL (Azure access token).
 */
async function apiFetch(path, accessToken, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
  })

  if (response.status === 401) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Unauthorized — token missing or invalid.')
  }

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${options.method || 'GET'} ${path} failed (${response.status}): ${text}`)
  }

  return response.json()
}

export function fetchMe(accessToken) {
  return apiFetch('/me', accessToken)
}

export function fetchProtected(accessToken) {
  return apiFetch('/protected', accessToken)
}
