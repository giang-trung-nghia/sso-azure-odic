import { PEER_APP_URL } from '../config'

/**
 * Educational panel: cross-app SSO expectations (Entra IdP vs per-app auth).
 */
export default function CrossAppSsoPanel({ azureOid, sessionAuth }) {
  return (
    <section className="card sso-panel">
      <h2>Cross-app SSO (fe-1 ↔ fe-2)</h2>
      <p className="muted">
        Both apps trust <strong>the same Entra tenant</strong>. SSO at Microsoft does{' '}
        <em>not</em> automatically log you into the other app — each app still creates its own
        session or token.
      </p>

      <dl className="kv">
        <dt>This app (fe-1)</dt>
        <dd>Django <code>sessionid</code> cookie → Redis</dd>
        <dt>Other app</dt>
        <dd>
          <a href={PEER_APP_URL} target="_blank" rel="noreferrer">
            fe-2 (MSAL + Bearer JWT)
          </a>
        </dd>
        <dt>azure_oid (compare)</dt>
        <dd>
          <code>{azureOid || '—'}</code>
        </dd>
      </dl>

      {sessionAuth && (
        <dl className="kv">
          <dt>Session expires</dt>
          <dd>{sessionAuth.session_expires_at || '—'}</dd>
          <dt>In</dt>
          <dd>
            {sessionAuth.session_expires_in_seconds != null
              ? `${sessionAuth.session_expires_in_seconds}s`
              : '—'}
          </dd>
        </dl>
      )}

      <ol className="flow">
        <li>Log in here first, then open fe-2 — Microsoft login should be quick (same Entra account).</li>
        <li>fe-2 still needs its own MSAL login (separate browser storage).</li>
        <li>Compare <code>azure_oid</code> on both dashboards — they should match.</li>
        <li>Logout here clears Django + Entra; fe-2 may still have MSAL tokens until its logout.</li>
      </ol>

      <p className="muted">
        Full test checklist: <code>docs/cross-app-sso.md</code> in the repo.
      </p>
    </section>
  )
}
