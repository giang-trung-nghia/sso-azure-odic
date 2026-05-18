/**
 * Django API base URL (browser → be-1-django).
 *
 * Entra redirect URI for this project: http://localhost:8001/oidc/callback/
 * Use localhost (not 127.0.0.1) for fe-1 and Django so the session cookie matches.
 */
export const API_BASE = (
  import.meta.env.VITE_API_URL_BE1 || 'http://localhost:8001'
).replace(/\/$/, '')

export const PEER_APP_URL = (
  import.meta.env.VITE_FE2_URL || 'http://localhost:5172'
).replace(/\/$/, '')
