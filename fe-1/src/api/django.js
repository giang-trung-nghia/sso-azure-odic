import { API_BASE } from '../config'

async function parseJsonResponse(response, label) {
  if (response.status === 401) {
    return { authenticated: false }
  }
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${label} failed (${response.status}): ${text}`)
  }
  return response.json()
}

/**
 * Session cookie auth: always send credentials so Django sessionid is included.
 */
export async function fetchApiMe() {
  const response = await fetch(`${API_BASE}/api/me/`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })
  return parseJsonResponse(response, 'GET /api/me/')
}

/** @deprecated use fetchApiMe — same payload */
export async function fetchMe() {
  return fetchApiMe()
}

export function startLogin() {
  const next = `${window.location.origin}/dashboard`
  window.location.href = `${API_BASE}/accounts/login/?next=${encodeURIComponent(next)}`
}

export function startLogout() {
  window.location.href = `${API_BASE}/oidc/logout/`
}
