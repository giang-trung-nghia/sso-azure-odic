import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { API_BASE, API_SCOPE, MSAL_CONFIGURED } from '../config'
import { loginRequest } from '../auth/msal'

export default function LoginPage() {
  const { instance } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleLogin = () => {
    instance.loginPopup(loginRequest).catch(console.error)
  }

  return (
    <main className="page">
      <h1>fe-2 — Bearer JWT login</h1>
      <p className="muted">
        This app talks only to <code>{API_BASE}</code>. MSAL obtains an Azure{' '}
        <strong>access token</strong>; each API call sends{' '}
        <code>Authorization: Bearer …</code>.
      </p>

      <section className="card">
        <h2>JWT flow vs fe-1 (Django session)</h2>
        <table className="compare">
          <thead>
            <tr>
              <th></th>
              <th>fe-1 + Django</th>
              <th>fe-2 + FastAPI</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Proof of login</td>
              <td>
                <code>sessionid</code> cookie
              </td>
              <td>Bearer access token</td>
            </tr>
            <tr>
              <td>Stored in browser</td>
              <td>Cookie (session id only)</td>
              <td>MSAL cache (sessionStorage)</td>
            </tr>
            <tr>
              <td>API request</td>
              <td>
                <code>credentials: include</code>
              </td>
              <td>
                <code>Authorization: Bearer</code>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="card muted">
        <h2>Token acquisition (short)</h2>
        <ol className="flow">
          <li>MSAL opens Microsoft login (popup).</li>
          <li>Entra returns tokens; MSAL stores them in sessionStorage.</li>
          <li>
            <code>acquireTokenSilent</code> refreshes access token for scope{' '}
            <code>{API_SCOPE || '(configure VITE_AZURE_API_SCOPE)'}</code>.
          </li>
          <li>fe-2 attaches token to FastAPI requests; server validates via JWKS.</li>
        </ol>
      </section>

      {!MSAL_CONFIGURED ? (
        <p className="warn">
          Set <code>VITE_AZURE_CLIENT_ID</code> and <code>VITE_AZURE_TENANT_ID</code> (see
          .env.example). Register a <strong>Single-page application</strong> redirect URI:{' '}
          <code>{window.location.origin}</code>
        </p>
      ) : (
        <button type="button" className="primary" onClick={handleLogin}>
          Login with Microsoft
        </button>
      )}
    </main>
  )
}
