/**
 * Django API base URL (browser → be-1-django).
 * Set via VITE_API_URL_BE1 in .env / docker-compose.
 */
export const API_BASE = (
  import.meta.env.VITE_API_URL_BE1 || 'http://127.0.0.1:8001'
).replace(/\/$/, '')
