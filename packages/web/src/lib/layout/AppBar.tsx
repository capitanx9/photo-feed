'use client'

import { useRouter } from 'next/navigation'
import NextLink from 'next/link'
import {
  AppBar as MuiAppBar,
  Badge,
  Box,
  Button,
  Container,
  IconButton,
  Stack,
  Toolbar,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import ShoppingCartOutlinedIcon from '@mui/icons-material/ShoppingCartOutlined'
import { useAuth } from '@/lib/auth/useAuth'
import { useCart } from '@/lib/cart/useCart'
import { useUIStore } from '@/store/ui'
import { CartDrawer } from '@/lib/cart/CartDrawer'
import { t } from '@/lib/i18n/t'

export function TopBar({ locale }: { locale: string }) {
  const { user, isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const { data: cart } = useCart()
  const cartOpen = useUIStore((s) => s.cartOpen)
  const openCart = useUIStore((s) => s.openCart)
  const closeCart = useUIStore((s) => s.closeCart)

  const cartCount = cart?.items.reduce((acc, it) => acc + it.qty, 0) ?? 0

  const handleLogout = async () => {
    await logout()
    router.replace(`/${locale}/login`)
  }

  return (
    <>
      <MuiAppBar
        position="sticky"
        color="default"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
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
                <Button
                  component={NextLink}
                  href={`/${locale}/orders`}
                  size="small"
                  variant="text"
                >
                  {t('nav.orders')}
                </Button>
                <IconButton onClick={openCart} aria-label={t('cart.open')}>
                  <Badge badgeContent={cartCount} color="primary" overlap="circular">
                    <ShoppingCartOutlinedIcon />
                  </Badge>
                </IconButton>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {user.email}
                </Typography>
                <Button onClick={handleLogout} size="small" variant="outlined">
                  {t('auth.logout')}
                </Button>
              </Stack>
            ) : (
              <Button
                component={NextLink}
                href={`/${locale}/login`}
                size="small"
                variant="outlined"
              >
                {t('auth.login.submit')}
              </Button>
            )}
          </Toolbar>
        </Container>
      </MuiAppBar>
      <CartDrawer open={cartOpen} onClose={closeCart} locale={locale} />
    </>
  )
}
