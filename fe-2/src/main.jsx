import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { initializeMsal } from './auth/msal'
import App from './App.jsx'
import './index.css'

initializeMsal().then(() => {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
