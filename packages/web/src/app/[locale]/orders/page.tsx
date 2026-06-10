'use client'

import { useCallback } from 'react'
import { useParams } from 'next/navigation'
import NextLink from 'next/link'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Stack,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import { TopBar } from '@/lib/layout/AppBar'
import { AuthGuard } from '@/lib/auth/AuthGuard'
import { useOrders } from '@/lib/orders/useOrders'
import { useInfiniteSentinel } from '@/lib/posts/useInfiniteSentinel'
import { t } from '@/lib/i18n/t'
import type { Order } from '@/lib/api/orders'

export default function OrdersPage() {
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  return (
    <>
      <TopBar locale={locale} />
      <AuthGuard locale={locale}>
        <OrdersList locale={locale} />
      </AuthGuard>
    </>
  )
}

function OrdersList({ locale }: { locale: string }) {
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useOrders()

  const onIntersect = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) void fetchNextPage()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const sentinelRef = useInfiniteSentinel(onIntersect, hasNextPage ?? false)

  const orders: Order[] = data?.pages.flatMap((p) => p.results) ?? []

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        {t('orders.heading')}
      </Typography>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && <Alert severity="error">{error?.message ?? t('orders.loadError')}</Alert>}

      {!isLoading && !isError && orders.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" sx={{ color: 'text.secondary', mb: 2 }}>
            {t('orders.empty')}
          </Typography>
          <Button component={NextLink} href={`/${locale}`} variant="contained">
            {t('post.detail.backHome')}
          </Button>
        </Box>
      )}

      <Stack spacing={2}>
        {orders.map((o) => (
          <OrderRow key={o.id} order={o} locale={locale} />
        ))}
      </Stack>

      <Box ref={sentinelRef} sx={{ height: 1 }} />
      {isFetchingNextPage && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}
    </Container>
  )
}

function OrderRow({ order, locale }: { order: Order; locale: string }) {
  return (
    <MuiLink
      component={NextLink}
      href={`/${locale}/orders/${order.id}`}
      underline="none"
      color="inherit"
    >
      <Box
        sx={{
          p: 2,
          border: 1,
          borderColor: 'divider',
          borderRadius: 2,
          bgcolor: 'background.paper',
          '&:hover': { borderColor: 'primary.main' },
        }}
      >
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}
        >
          <Box>
            <Typography variant="subtitle1">
              {t('orders.row.id', { id: order.id })}
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {new Date(order.created_at).toLocaleString()}
            </Typography>
          </Box>
          <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
            <Chip
              size="small"
              label={order.status}
              color={
                order.status === 'paid'
                  ? 'success'
                  : order.status === 'cancelled'
                    ? 'default'
                    : 'info'
              }
            />
            <Typography variant="h6">${order.total}</Typography>
          </Stack>
        </Stack>
      </Box>
    </MuiLink>
  )
}
