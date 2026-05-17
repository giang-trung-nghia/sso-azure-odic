import { API_BASE } from '../config'

/**
 * Session cookie auth: always send credentials so Django sessionid is included.
 */
export async function fetchMe() {
  const response = await fetch(`${API_BASE}/accounts/me/`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })

  if (response.status === 401) {
    return { authenticated: false }
  }

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`GET /accounts/me/ failed (${response.status}): ${text}`)
  }

  return response.json()
}

/** Full-page navigation — required for OIDC redirect chain (not fetch). */
export function startLogin() {
  const next = `${window.location.origin}/dashboard`
  window.location.href = `${API_BASE}/accounts/login/?next=${encodeURIComponent(next)}`
}

/** Ends Django session and Entra logout; Django redirects back to fe-1. */
export function startLogout() {
  window.location.href = `${API_BASE}/oidc/logout/`
}
