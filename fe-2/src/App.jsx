import { MsalProvider } from '@azure/msal-react'
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import { msalInstance } from './auth/msal'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import './App.css'

export default function App() {
  return (
    <MsalProvider instance={msalInstance}>
      <BrowserRouter>
        <div className="app">
          <nav className="nav">
            <strong>fe-2</strong>
            <span className="muted">→ be-2-fastapi (Bearer JWT)</span>
            <Link to="/">Login</Link>
            <Link to="/dashboard">Dashboard</Link>
          </nav>
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </MsalProvider>
  )
}
