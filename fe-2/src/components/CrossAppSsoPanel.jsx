import { PEER_APP_URL } from '../config'

function formatTokenExp(exp) {
  if (!exp) return '—'
  const d = new Date(exp * 1000)
  return `${d.toISOString()} (${Math.max(0, Math.floor(exp - Date.now() / 1000))}s left)`
}

/**
 * Educational panel: cross-app SSO expectations (Entra IdP vs per-app auth).
 */
export default function CrossAppSsoPanel({ azureOid, tokenExp }) {
  return (
    <section className="card sso-panel">
      <h2>Cross-app SSO (fe-2 ↔ fe-1)</h2>
      <p className="muted">
        Entra is the <strong>central identity</strong>. fe-2 keeps access tokens in MSAL{' '}
        <code>sessionStorage</code>; fe-1 uses a Django cookie — they do not share storage.
      </p>

      <dl className="kv">
        <dt>This app (fe-2)</dt>
        <dd>Bearer access token (MSAL)</dd>
        <dt>Other app</dt>
        <dd>
          <a href={PEER_APP_URL} target="_blank" rel="noreferrer">
            fe-1 (Django session)
          </a>
        </dd>
        <dt>azure_oid (compare)</dt>
        <dd>
          <code>{azureOid || '—'}</code>
        </dd>
        <dt>Access token exp</dt>
        <dd>{formatTokenExp(tokenExp)}</dd>
      </dl>

      <ol className="flow">
        <li>Log in here first, then open fe-1 — Entra may skip password (SSO cookie at Microsoft).</li>
        <li>fe-1 still runs OIDC and sets its own <code>sessionid</code> cookie.</li>
        <li>Compare <code>azure_oid</code> — same person, two auth mechanisms.</li>
        <li>Logout here clears MSAL cache only; Django session on fe-1 may still work until its logout.</li>
      </ol>

      <p className="muted">
        Full test checklist: <code>docs/cross-app-sso.md</code> in the repo.
      </p>
    </section>
  )
}
