'use client'

import { useQueries } from '@tanstack/react-query'
import {
  Box,
  Button,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined'
import AddIcon from '@mui/icons-material/Add'
import RemoveIcon from '@mui/icons-material/Remove'
import NextLink from 'next/link'
import { useRouter } from 'next/navigation'
import { getPost, type Post } from '@/lib/api/posts'
import type { CartItem } from '@/lib/api/cart'
import {
  useCart,
  useRemoveCartItem,
  useUpdateCartItemQty,
} from '@/lib/cart/useCart'
import { t } from '@/lib/i18n/t'

type Props = {
  open: boolean
  onClose: () => void
  locale: string
}

export function CartDrawer({ open, onClose, locale }: Props) {
  const router = useRouter()
  const { data: cart, isLoading } = useCart()
  const items = cart?.items ?? []

  const goToCheckout = () => {
    onClose()
    router.push(`/${locale}/checkout`)
  }

  // Fetch the post for each line item (for thumbnail + caption).
  // Already-cached posts (from feed/detail) return instantly.
  const postQueries = useQueries({
    queries: items.map((it) => ({
      queryKey: ['post', it.post_id] as const,
      queryFn: () => getPost(it.post_id),
      staleTime: 60_000,
      enabled: open,
    })),
  })

  const postById: Record<number, Post | undefined> = {}
  postQueries.forEach((q, i) => {
    const it = items[i]
    if (it) postById[it.post_id] = q.data
  })

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{ paper: { sx: { width: { xs: '100%', sm: 420 } } } }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          {t('cart.heading')}
        </Typography>
        <IconButton onClick={onClose} aria-label={t('cart.close')}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : items.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            {t('cart.empty')}
          </Typography>
        </Box>
      ) : (
        <Stack sx={{ flexGrow: 1, overflow: 'auto' }}>
          {items.map((item) => (
            <CartLine
              key={item.id}
              item={item}
              post={postById[item.post_id]}
              locale={locale}
              onAfterRemove={onClose}
            />
          ))}
        </Stack>
      )}

      {items.length > 0 && cart && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Stack
              direction="row"
              spacing={2}
              sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 2 }}
            >
              <Typography variant="body1">{t('cart.total')}</Typography>
              <Typography variant="h6">${cart.total}</Typography>
            </Stack>
            <Button fullWidth variant="contained" size="large" onClick={goToCheckout}>
              {t('cart.checkout')}
            </Button>
          </Box>
        </>
      )}
    </Drawer>
  )
}

function CartLine({
  item,
  post,
  locale,
  onAfterRemove,
}: {
  item: CartItem
  post: Post | undefined
  locale: string
  onAfterRemove: () => void
}) {
  const updateQty = useUpdateCartItemQty()
  const removeItem = useRemoveCartItem()
  const thumb = post?.media[0]?.url

  return (
    <Box sx={{ p: 2, display: 'flex', gap: 2, borderBottom: 1, borderColor: 'divider' }}>
      <Box
        sx={{
          width: 72,
          height: 72,
          flexShrink: 0,
          borderRadius: 1,
          overflow: 'hidden',
          bgcolor: 'action.hover',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
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
          onClick={onAfterRemove}
        >
          <Typography
            variant="body2"
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {post?.caption || `Post #${item.post_id}`}
          </Typography>
        </MuiLink>
        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
          ${item.price}
        </Typography>

        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mt: 1 }}>
          <IconButton
            size="small"
            aria-label={t('cart.decrement')}
            disabled={item.qty <= 1 || updateQty.isPending}
            onClick={() => updateQty.mutate({ id: item.id, qty: item.qty - 1 })}
          >
            <RemoveIcon fontSize="small" />
          </IconButton>
          <Typography variant="body2" sx={{ minWidth: 24, textAlign: 'center' }}>
            {item.qty}
          </Typography>
          <IconButton
            size="small"
            aria-label={t('cart.increment')}
            disabled={updateQty.isPending}
            onClick={() => updateQty.mutate({ id: item.id, qty: item.qty + 1 })}
          >
            <AddIcon fontSize="small" />
          </IconButton>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton
            size="small"
            aria-label={t('cart.remove')}
            disabled={removeItem.isPending}
            onClick={() => removeItem.mutate(item.id)}
          >
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        </Stack>
      </Box>
    </Box>
  )
}
