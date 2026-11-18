// The access token lives only in memory. The refresh token is an HttpOnly
// cookie set by the backend, so page scripts can never read it.

let accessToken: string | null = null

// Tokens were kept in localStorage before; remove any leftovers.
try {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
} catch {
  // Storage may be unavailable (private mode); nothing to clean up then.
}

export const getAccessToken = (): string | null => accessToken

export const setAccessToken = (token: string | null): void => {
  accessToken = token
}
