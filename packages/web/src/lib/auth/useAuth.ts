import { useCallback } from 'react'
import { useAuthStore } from '@/store/auth'
import * as authApi from '@/lib/api/auth'
import type { LoginInput, RegisterInput } from './schemas'

// Thin wrapper around the Zustand store. Hides the auth API surface so
// pages don't import @/lib/api/auth directly — only this hook + the React
// Query mutations we'll add later for cache invalidation.
export function useAuth() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const clear = useAuthStore((s) => s.logout)

  const login = useCallback(
    async (input: LoginInput) => {
      // Django returns the user object plus sets the cookies.
      const u = await authApi.login(input)
      setUser(u)
      return u
    },
    [setUser],
  )

  const register = useCallback(
    async (input: RegisterInput) => {
      // /register does NOT log the user in (per docs/api/auth.md). Caller
      // should redirect to /login next.
      return authApi.register(input)
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      // Even if the server call fails (e.g. already expired), clear local
      // state so the UI doesn't lie about who's signed in.
      clear()
    }
  }, [clear])

  return { user, login, register, logout, isAuthenticated: user !== null }
}
