'use client'

import { useParams } from 'next/navigation'
import NextLink from 'next/link'
import { useQueries } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Stack,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import { TopBar } from '@/lib/layout/AppBar'
import { AuthGuard } from '@/lib/auth/AuthGuard'
import { useOrder } from '@/lib/orders/useOrders'
import { getPost, type Post } from '@/lib/api/posts'
import type { OrderItem } from '@/lib/api/orders'
import { t } from '@/lib/i18n/t'

export default function OrderDetailPage() {
  const params = useParams<{ locale: string; id: string }>()
  const locale = params.locale
  return (
    <>
      <TopBar locale={locale} />
      <AuthGuard locale={locale}>
        <OrderDetail locale={locale} id={Number(params.id)} />
      </AuthGuard>
    </>
  )
}

function OrderDetail({ locale, id }: { locale: string; id: number }) {
  const { data: order, isLoading, isError } = useOrder(id)
  const items = order?.items ?? []

  // Each line carries post_id only; fetch the post for thumbnail + caption.
  // Already-cached posts (feed/detail/cart) come back instantly.
  const postQueries = useQueries({
    queries: items.map((it) => ({
      queryKey: ['post', it.post_id] as const,
      queryFn: () => getPost(it.post_id),
      staleTime: 60_000,
    })),
  })

  const postById: Record<number, Post | undefined> = {}
  postQueries.forEach((q, i) => {
    const it = items[i]
    if (it) postById[it.post_id] = q.data
  })

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <MuiLink
        component={NextLink}
        href={`/${locale}/orders`}
        underline="hover"
        sx={{ display: 'inline-block', mb: 3 }}
      >
        {t('orders.detail.backToList')}
      </MuiLink>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && <Alert severity="error">{t('orders.detail.loadError')}</Alert>}

      {order && (
        <Stack spacing={3}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
            sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}
          >
            <Box>
              <Typography variant="h4" component="h1">
                {t('orders.row.id', { id: order.id })}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {new Date(order.created_at).toLocaleString()}
              </Typography>
            </Box>
            <Chip
              label={order.status}
              color={
                order.status === 'paid'
                  ? 'success'
                  : order.status === 'cancelled'
                    ? 'default'
                    : 'info'
              }
            />
          </Stack>

          <Box
            sx={{
              p: 3,
              border: 1,
              borderColor: 'divider',
              borderRadius: 2,
              bgcolor: 'background.paper',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              {t('orders.detail.items')}
            </Typography>
            <Stack divider={<Divider />} spacing={2}>
              {items.map((it) => (
                <OrderItemRow key={it.id} item={it} post={postById[it.post_id]} locale={locale} />
              ))}
            </Stack>
            <Divider sx={{ my: 2 }} />
            <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
              <Typography variant="subtitle1">{t('cart.total')}</Typography>
              <Typography variant="h6">${order.total}</Typography>
            </Stack>
          </Box>

          <Box
            sx={{
              p: 3,
              border: 1,
              borderColor: 'divider',
              borderRadius: 2,
              bgcolor: 'background.paper',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              {t('orders.detail.shipping')}
            </Typography>
            <Stack spacing={0.5}>
              <Typography variant="body2">{order.shipping_name}</Typography>
              <Typography variant="body2">{order.shipping_address}</Typography>
              <Typography variant="body2">
                {order.shipping_city}, {order.shipping_zip}
              </Typography>
              {order.shipping_country && (
                <Typography variant="body2">{order.shipping_country}</Typography>
              )}
            </Stack>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 2 }}>
              {t('orders.detail.paidWith', { method: order.payment_method })}
            </Typography>
          </Box>
        </Stack>
      )}
    </Container>
  )
}

function OrderItemRow({
  item,
  post,
  locale,
}: {
  item: OrderItem
  post: Post | undefined
  locale: string
}) {
  const thumb = post?.media[0]?.url
  return (
    <Stack direction="row" spacing={2}>
      <Box
        sx={{
          width: 64,
          height: 64,
          flexShrink: 0,
          borderRadius: 1,
          overflow: 'hidden',
          bgcolor: 'action.hover',
        }}
      >
        {thumb && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={thumb}
            alt={post?.caption || `post ${item.post_id}`}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        )}
      </Box>
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        <MuiLink
          component={NextLink}
          href={`/${locale}/posts/${item.post_id}`}
          underline="hover"
          color="inherit"
        >
          <Typography variant="body2">{post?.caption || `Post #${item.post_id}`}</Typography>
        </MuiLink>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          ${item.price_at_purchase} × {item.qty}
        </Typography>
      </Box>
      <Typography variant="body1" sx={{ alignSelf: 'center' }}>
        ${(Number(item.price_at_purchase) * item.qty).toFixed(2)}
      </Typography>
    </Stack>
  )
}
