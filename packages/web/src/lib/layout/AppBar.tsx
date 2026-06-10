'use client'

import { useRouter } from 'next/navigation'
import NextLink from 'next/link'
import {
  AppBar as MuiAppBar,
  Box,
  Button,
  Container,
  Stack,
  Toolbar,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import { useAuth } from '@/lib/auth/useAuth'
import { t } from '@/lib/i18n/t'

export function TopBar({ locale }: { locale: string }) {
  const { user, isAuthenticated, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.replace(`/${locale}/login`)
  }

  return (
    <MuiAppBar position="sticky" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Container maxWidth="md">
        <Toolbar disableGutters sx={{ gap: 2 }}>
          <MuiLink
            component={NextLink}
            href={`/${locale}`}
            underline="none"
            color="inherit"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Typography variant="h6" component="span">
              {t('app.title')}
            </Typography>
          </MuiLink>

          <Box sx={{ flexGrow: 1 }} />

          {isAuthenticated && user ? (
            <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
              <Button
                component={NextLink}
                href={`/${locale}/posts/new`}
                size="small"
                variant="contained"
              >
                {t('nav.newPost')}
              </Button>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {user.email}
              </Typography>
              <Button onClick={handleLogout} size="small" variant="outlined">
                {t('auth.logout')}
              </Button>
            </Stack>
          ) : (
            <Button component={NextLink} href={`/${locale}/login`} size="small" variant="outlined">
              {t('auth.login.submit')}
            </Button>
          )}
        </Toolbar>
      </Container>
    </MuiAppBar>
  )
}
