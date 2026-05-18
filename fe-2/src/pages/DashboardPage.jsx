import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { fetchMe, fetchProtected } from '../api/fastapi'
import { loginRequest } from '../auth/msal'
import { useAccessToken } from '../auth/useAccessToken'
import { API_BASE } from '../config'

export default function DashboardPage() {
  const isAuthenticated = useIsAuthenticated()
  const { instance } = useMsal()
  const { account, acquire, error: tokenError } = useAccessToken()

  const [me, setMe] = useState(null)
  const [protectedData, setProtectedData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadApis = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const accessToken = await acquire()
      if (!accessToken) {
        setMe(null)
        setProtectedData(null)
        return
      }
      const [meData, protectedRes] = await Promise.all([
        fetchMe(accessToken),
        fetchProtected(accessToken),
      ])
      setMe(meData)
      setProtectedData(protectedRes)
    } catch (err) {
      setError(err.message)
      setMe(null)
      setProtectedData(null)
    } finally {
      setLoading(false)
    }
  }, [acquire])

  useEffect(() => {
    if (isAuthenticated) {
      loadApis()
    }
  }, [isAuthenticated, loadApis])

  const handleLogin = () => {
    instance.loginPopup(loginRequest).catch(console.error)
  }

  const handleLogout = () => {
    instance
      .logoutPopup({ account, postLogoutRedirectUri: window.location.origin })
      .catch(console.error)
  }

  if (!isAuthenticated) {
    return (
      <main className="page">
        <h1>Dashboard</h1>
        <p className="warn">Not signed in with MSAL.</p>
        <button type="button" className="primary" onClick={handleLogin}>
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
        <button type="button" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <p className="ok">Authenticated with Azure (MSAL). API calls use Bearer JWT.</p>

      {account && (
        <p className="muted">
          MSAL account: <strong>{account.username}</strong>
        </p>
      )}

      {(tokenError || error) && (
        <pre className="error">{tokenError || error}</pre>
      )}

      {loading && <p>Loading FastAPI…</p>}

      <section className="card">
        <h2>
          <code>GET /me</code>
        </h2>
        {me ? (
          <pre className="json">{JSON.stringify(me, null, 2)}</pre>
        ) : (
          !loading && <p className="muted">No data yet.</p>
        )}
      </section>

      <section className="card">
        <h2>
          <code>GET /protected</code>
        </h2>
        {protectedData ? (
          <pre className="json">{JSON.stringify(protectedData, null, 2)}</pre>
        ) : (
          !loading && <p className="muted">No data yet.</p>
        )}
        <button type="button" onClick={loadApis} disabled={loading}>
          Refresh APIs
        </button>
      </section>

      <section className="card muted">
        <h2>How Bearer requests work</h2>
        <p>
          <code>fetch</code> to <code>{API_BASE}</code> includes{' '}
          <code>Authorization: Bearer &lt;access_token&gt;</code>. FastAPI validates signature,
          issuer, audience, expiration, and tenant — no Redis session. Compare with fe-1, which
          sends the Django <code>sessionid</code> cookie instead.
        </p>
      </section>
    </main>
  )
}
