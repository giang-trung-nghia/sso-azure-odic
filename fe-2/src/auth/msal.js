import { PublicClientApplication } from '@azure/msal-browser'
import { AZURE_CLIENT_ID, AZURE_TENANT_ID, API_SCOPE } from '../config'

export const loginRequest = {
  scopes: [API_SCOPE],
}

export const msalConfig = {
  auth: {
    clientId: AZURE_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${AZURE_TENANT_ID}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
    navigateToLoginRequestUrl: false,
  },
  cache: {
    // Educational default: tokens live in sessionStorage (tab-scoped).
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
}

export const msalInstance = new PublicClientApplication(msalConfig)

/** Call once before rendering React (see main.jsx). */
export async function initializeMsal() {
  await msalInstance.initialize()
  await msalInstance.handleRedirectPromise()
}
