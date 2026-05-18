import { useCallback, useState } from 'react'
import { useMsal } from '@azure/msal-react'
import { loginRequest } from './msal'

/**
 * Acquire an access token for be-2-fastapi (silent, then popup if needed).
 */
export function useAccessToken() {
  const { instance, accounts } = useMsal()
  const [token, setToken] = useState(null)
  const [error, setError] = useState(null)

  const acquire = useCallback(async () => {
    setError(null)
    const account = accounts[0]
    if (!account) {
      setToken(null)
      return null
    }

    try {
      const result = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      })
      setToken(result.accessToken)
      return result.accessToken
    } catch {
      try {
        const result = await instance.acquireTokenPopup(loginRequest)
        setToken(result.accessToken)
        return result.accessToken
      } catch (popupError) {
        setError(popupError.message || String(popupError))
        setToken(null)
        throw popupError
      }
    }
  }, [instance, accounts])

  return { token, error, acquire, account: accounts[0] }
}
