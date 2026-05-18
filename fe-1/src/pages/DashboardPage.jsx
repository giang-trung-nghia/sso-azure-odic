import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchApiMe, startLogin, startLogout } from '../api/django'
import CrossAppSsoPanel from '../components/CrossAppSsoPanel'
import { API_BASE } from '../config'

export default function DashboardPage() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadMe = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchApiMe()
      if (!data.authenticated) {
        setUser(null)
      } else {
        setUser(data)
      }
    } catch (err) {
      setError(err.message)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMe()
  }, [loadMe])

  if (loading) {
    return (
      <main className="page">
        <p>Checking session…</p>
      </main>
    )
  }

  if (!user?.authenticated) {
    return (
      <main className="page">
        <h1>Dashboard</h1>
        <p className="warn">Not signed in (no Django session cookie for {API_BASE}).</p>
        {error && <pre className="error">{error}</pre>}
        <button type="button" className="primary" onClick={startLogin}>
          Login with Microsoft
        </button>
        <p className="muted">
          <Link to="/">Back to login page</Link>
        </p>
      </main>
    )
  }

  const groups = user.groups || []

  return (
    <main className="page">
      <header className="row">
        <h1>Dashboard</h1>
        <button type="button" onClick={startLogout}>
          Logout
        </button>
      </header>

      <p className="ok">Authenticated via Django session cookie.</p>

      <section className="card">
        <h2>Identity (<code>GET /api/me/</code>)</h2>
        <dl className="kv">
          <dt>username</dt>
          <dd>{user.username}</dd>
          <dt>email</dt>
          <dd>{user.email || '—'}</dd>
          <dt>azure_oid</dt>
          <dd>
            <code>{user.azure_oid || '—'}</code>
          </dd>
          <dt>tenant_id</dt>
          <dd>
            <code>{user.tenant_id || '—'}</code>
          </dd>
          <dt>display_name</dt>
          <dd>{user.display_name || '—'}</dd>
          <dt>last_synced_at</dt>
          <dd>{user.last_synced_at || '—'}</dd>
        </dl>
        <button type="button" onClick={loadMe}>
          Refresh /api/me
        </button>
      </section>

      <section className="card">
        <h2>
          Azure groups ({groups.length}) — object IDs + Graph display names
        </h2>
        {groups.length === 0 ? (
          <p className="warn">
            No groups stored. Add optional <code>groups</code> claim in Entra, grant{' '}
            <code>GroupMember.Read.All</code>, set <code>OIDC_STORE_ACCESS_TOKEN=1</code>, then
            log in again.
          </p>
        ) : (
          <table className="groups-table">
            <thead>
              <tr>
                <th>display_name</th>
                <th>object_id</th>
                <th>security</th>
                <th>resolved_at</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => (
                <tr key={g.object_id}>
                  <td>{g.display_name || <em className="muted">(unresolved)</em>}</td>
                  <td>
                    <code>{g.object_id}</code>
                  </td>
                  <td>{g.security_enabled == null ? '—' : String(g.security_enabled)}</td>
                  <td className="muted">{g.resolved_at || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted">
          Group object IDs: <code>{user.group_object_ids?.join(', ') || '—'}</code>
        </p>
      </section>

      <section className="card muted">
        <h2>Raw JSON (debug)</h2>
        <pre className="json">{JSON.stringify(user, null, 2)}</pre>
      </section>

      <CrossAppSsoPanel azureOid={user.azure_oid} sessionAuth={user.auth} />

      <section className="card muted">
        <h2>How this request works</h2>
        <p>
          After login, Django syncs Entra <strong>group GUIDs</strong> from OIDC claims into
          PostgreSQL, calls <strong>Microsoft Graph</strong> to resolve{' '}
          <strong>display names</strong>, then <code>GET /api/me/</code> returns everything with{' '}
          <code>credentials: &quot;include&quot;</code>.
        </p>
      </section>
    </main>
  )
}
