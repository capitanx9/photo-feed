import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

// Same-origin API. We deliberately don't set `baseURL` so every request
// hits the page's origin (`https://photo-feed.gotdns.ch` in prod,
// `http://localhost:3000` in dev). nginx routes `/api/` to Django on
// prod; the `rewrites()` block in next.config.ts proxies `/api/` to
// the local Django runserver in dev.
//
// Why same-origin instead of NEXT_PUBLIC_API_URL: those vars get baked
// in at build time, which means one image per environment and a long
// CORS / credentials configuration tail. Same-origin sidesteps all of
// it — one image runs anywhere, cookies just work, no CORS at all.
//
// withCredentials is still on because axios defaults it off for *all*
// requests, and we need cookies attached to refresh/login responses.
export const apiClient = axios.create({
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Accept-Language interceptor (L5-prep-3 from the plan).
// Lab 4 hardcodes 'en'. Lab 5 will read the current locale from the auth/locale
// Zustand store and set it dynamically here — no changes to call sites.
apiClient.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = 'en'
  return config
})

// ---------------------------------------------------------------------
// 401 → refresh → retry
//
// One in-flight refresh at a time: concurrent 401s share the same promise
// so we don't fire /refresh five times. After the refresh resolves, all
// queued requests retry with the new access cookie. If the refresh itself
// fails (refresh token expired/revoked), we clear the store and let the
// caller handle redirect.
// ---------------------------------------------------------------------

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

let refreshInFlight: Promise<void> | null = null

async function performRefresh(): Promise<void> {
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = apiClient
    .post('/api/auth/refresh/')
    .then(() => undefined)
    .finally(() => {
      refreshInFlight = null
    })
  return refreshInFlight
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const status = error.response?.status

    // Don't loop on the refresh call itself, and only retry once per request.
    const isRefreshCall = original?.url?.includes('/api/auth/refresh/')
    if (status !== 401 || !original || original._retry || isRefreshCall) {
      return Promise.reject(error)
    }

    original._retry = true
    try {
      await performRefresh()
    } catch {
      // Refresh failed → clear local auth state. Don't redirect from here;
      // pages decide via the auth guard or the rejected mutation.
      const { useAuthStore } = await import('@/store/auth')
      useAuthStore.getState().logout()
      return Promise.reject(error)
    }
    return apiClient.request(original)
  },
)
