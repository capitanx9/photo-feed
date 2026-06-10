'use client'

import { Box, Button, Container, Stack, Typography, Link as MuiLink } from '@mui/material'
import NextLink from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api/client'
import { useAuth } from '@/lib/auth/useAuth'
import { t } from '@/lib/i18n/t'
import type { components } from '@/lib/api/schema'

type Health = components['schemas']['Health']

function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await apiClient.get<Health>('/api/health/')
      return res.data
    },
  })
}

export default function HomePage() {
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  const router = useRouter()
  const { user, isAuthenticated, logout } = useAuth()
  const { data, isLoading, isError } = useHealth()

  const status = isLoading
    ? t('smoke.health.checking')
    : isError
      ? t('smoke.health.error')
      : data?.ok
        ? t('smoke.health.ok')
        : t('smoke.health.error')

  const handleLogout = async () => {
    await logout()
    router.replace(`/${locale}/login`)
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Stack spacing={3}>
        <Typography variant="h3" component="h1">
          {t('smoke.heading')}
        </Typography>

        <Box>
          <Typography variant="body1">{status}</Typography>
        </Box>

        <Box>
          {isAuthenticated && user ? (
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
              <Typography variant="body1">
                {t('smoke.greeting', { email: user.email })}
              </Typography>
              <MuiLink component={NextLink} href={`/${locale}/posts/new`} underline="hover">
                {t('smoke.newPost')}
              </MuiLink>
              <Button onClick={handleLogout} variant="outlined" size="small">
                {t('auth.logout')}
              </Button>
            </Stack>
          ) : (
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Typography variant="body1">{t('smoke.anon')}</Typography>
              <MuiLink component={NextLink} href={`/${locale}/login`} underline="hover">
                {t('auth.login.submit')}
              </MuiLink>
            </Stack>
          )}
        </Box>
      </Stack>
    </Container>
  )
}
