/** FastAPI base URL — fe-2 talks only to be-2-fastapi. */
export const API_BASE = (
  import.meta.env.VITE_API_URL_BE2 || 'http://127.0.0.1:8002'
).replace(/\/$/, '')

export const AZURE_CLIENT_ID = import.meta.env.VITE_AZURE_CLIENT_ID || ''
export const AZURE_TENANT_ID = import.meta.env.VITE_AZURE_TENANT_ID || ''

/**
 * Scope for access tokens FastAPI will accept (aud claim).
 * Default: api://{clientId}/.default — register "Expose an API" in Entra if needed.
 */
export const API_SCOPE =
  import.meta.env.VITE_AZURE_API_SCOPE ||
  (AZURE_CLIENT_ID ? `api://${AZURE_CLIENT_ID}/.default` : '')

export const MSAL_CONFIGURED = Boolean(AZURE_CLIENT_ID && AZURE_TENANT_ID && API_SCOPE)
