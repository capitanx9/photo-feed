import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

// Minimal current-user shape for PR-1. PR-2 (auth) will fetch the real user
// from /api/auth/me/ and replace this; nothing here is load-bearing yet.
export type CurrentUser = {
  id: number
  email: string
  displayName?: string
}

type AuthState = {
  user: CurrentUser | null
  // L5-prep-7: idle-timer plumbing. Lab 4 sets this on login but doesn't read
  // it; Lab 5 adds react-idle-timer that uses this for the 15-min sign-off
  // popup. Store shape is fixed now so persisted state doesn't need migration.
  lastActivityAt: number | null
  setUser: (user: CurrentUser | null) => void
  touchActivity: () => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      lastActivityAt: null,
      setUser: (user) =>
        set({
          user,
          lastActivityAt: user ? Date.now() : null,
        }),
      touchActivity: () => set({ lastActivityAt: Date.now() }),
      logout: () => set({ user: null, lastActivityAt: null }),
    }),
    {
      name: 'photo-feed-auth',
      // Per the plan: brief is "сохранены на все время сессии" — sessionStorage
      // survives reload within the same tab but resets across tabs.
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
)
