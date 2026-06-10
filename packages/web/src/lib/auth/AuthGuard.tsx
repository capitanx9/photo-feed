'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { Box, CircularProgress } from '@mui/material'
import { useAuthStore } from '@/store/auth'
import { me } from '@/lib/api/auth'

// Wrap any private page. On mount, calls /api/auth/me/ once to verify the
// access cookie is still valid (the refresh-interceptor in api/client.ts
// transparently rotates it). If /me 401s — refresh already failed inside the
// interceptor and the store was cleared — we send the user to /en/login.
export function AuthGuard({ children, locale }: { children: ReactNode; locale: string }) {
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    let cancelled = false
    me()
      .then((u) => {
        if (!cancelled) setUser(u)
      })
      .catch(() => {
        if (!cancelled) {
          setUser(null)
          router.replace(`/${locale}/login`)
        }
      })
      .finally(() => {
        if (!cancelled) setChecked(true)
      })
    return () => {
      cancelled = true
    }
  }, [router, locale, setUser])

  if (!checked || !user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <CircularProgress />
      </Box>
    )
  }
  return <>{children}</>
}
