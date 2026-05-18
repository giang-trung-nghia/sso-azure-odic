import { startLogin } from '../api/django'
import { API_BASE } from '../config'

export default function LoginPage() {
  return (
    <main className="page">
      <h1>fe-1 — Django session login</h1>
      <p className="muted">
        API host: <code>{API_BASE}</code> — open fe-1 at{' '}
        <code>http://localhost:5171</code> to match Entra’s redirect URI{' '}
        <code>http://localhost:8001/oidc/callback/</code>.
        Login uses Microsoft via
        Django (OIDC); the browser stores a <strong>session cookie</strong>, not a JWT.
      </p>

      <section className="card">
        <h2>Session cookie flow (short)</h2>
        <ol className="flow">
          <li>You click Login → browser goes to Django → Entra.</li>
          <li>After sign-in, Django creates a server-side session (Redis).</li>
          <li>Django sets <code>sessionid</code> cookie for the API host.</li>
          <li>
            Later, <code>fetch(..., {'{ credentials: "include" }'})</code> sends that
            cookie; Django loads the session and knows who you are.
          </li>
        </ol>
        <p className="muted">
          fe-1 does <strong>not</strong> store or attach Bearer tokens — that pattern is
          for fe-2 + FastAPI.
        </p>
      </section>

      <button type="button" className="primary" onClick={startLogin}>
        Login with Microsoft
      </button>
    </main>
  )
}
