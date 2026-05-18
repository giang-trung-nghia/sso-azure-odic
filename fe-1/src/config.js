/**
 * Django API base URL (browser → be-1-django).
 * Set via VITE_API_URL_BE1 in .env / docker-compose.
 */
export const API_BASE = (
  import.meta.env.VITE_API_URL_BE1 || 'http://127.0.0.1:8001'
).replace(/\/$/, '')

export const PEER_APP_URL = (
  import.meta.env.VITE_FE2_URL || 'http://127.0.0.1:5172'
).replace(/\/$/, '')
