import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchMe, startLogin, startLogout } from '../api/django'
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
      const data = await fetchMe()
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
        <h2>Current user (<code>GET /accounts/me/</code>)</h2>
        <dl className="kv">
          <dt>username</dt>
          <dd>{user.username}</dd>
          <dt>email</dt>
          <dd>{user.email || '—'}</dd>
          <dt>azure_oid</dt>
          <dd>
            <code>{user.azure_oid || '—'}</code>
          </dd>
          <dt>is_staff</dt>
          <dd>{String(user.is_staff)}</dd>
        </dl>
        <button type="button" onClick={loadMe}>
          Refresh /me
        </button>
      </section>

      <CrossAppSsoPanel azureOid={user.azure_oid} sessionAuth={user.auth} />

      <section className="card muted">
        <h2>How this request works</h2>
        <p>
          <code>fetchMe()</code> calls <code>{API_BASE}/accounts/me/</code> with{' '}
          <code>credentials: &quot;include&quot;</code>. The browser attaches the{' '}
          <code>sessionid</code> cookie issued by Django after OIDC login. Django reads
          session data from Redis and returns JSON — no JWT in the frontend.
        </p>
      </section>
    </main>
  )
}
