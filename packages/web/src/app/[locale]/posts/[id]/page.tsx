'use client'

import { useParams } from 'next/navigation'
import NextLink from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Link as MuiLink,
  Stack,
  Typography,
} from '@mui/material'
import { TopBar } from '@/lib/layout/AppBar'
import { getPost } from '@/lib/api/posts'
import { useAuth } from '@/lib/auth/useAuth'
import { useAddToCart, useCart } from '@/lib/cart/useCart'
import { useUIStore } from '@/store/ui'
import { t } from '@/lib/i18n/t'

export default function PostDetailPage() {
  const params = useParams<{ locale: string; id: string }>()
  const locale = params.locale
  const id = Number(params.id)
  const { user } = useAuth()

  const { data: post, isLoading, isError } = useQuery({
    queryKey: ['post', id],
    queryFn: () => getPost(id),
    enabled: Number.isFinite(id),
  })

  const imageUrl = post?.media[0]?.url
  const isOwner = !!user && !!post && user.id === post.owner_id
  const { data: cart } = useCart()
  const addToCart = useAddToCart()
  const openCart = useUIStore((s) => s.openCart)
  const inCart = !!cart?.items.find((it) => it.post_id === id)

  return (
    <>
      <TopBar locale={locale} />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Stack spacing={3}>
          <MuiLink
            component={NextLink}
            href={`/${locale}`}
            underline="hover"
            sx={{ alignSelf: 'flex-start' }}
          >
            {t('post.detail.backHome')}
          </MuiLink>

          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          )}

          {isError && <Alert severity="error">{t('post.detail.loadError')}</Alert>}

          {post && (
            <Box
              sx={{
                border: 1,
                borderColor: 'divider',
                borderRadius: 2,
                overflow: 'hidden',
                bgcolor: 'background.paper',
              }}
            >
              {imageUrl && (
                <Box sx={{ bgcolor: 'action.hover', display: 'flex', justifyContent: 'center' }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={imageUrl}
                    alt={post.caption || `post ${post.id}`}
                    style={{ width: '100%', maxHeight: 720, objectFit: 'contain' }}
                  />
                </Box>
              )}
              <Box sx={{ p: 3 }}>
                <Stack spacing={2}>
                  {post.caption && <Typography variant="body1">{post.caption}</Typography>}
                  {post.price && (
                    <Typography variant="h5" sx={{ color: 'primary.main' }}>
                      ${post.price}
                    </Typography>
                  )}
                  <Stack
                    direction="row"
                    spacing={2}
                    sx={{ alignItems: 'center', flexWrap: 'wrap' }}
                  >
                    {post.price && !isOwner && (
                      inCart ? (
                        <Button variant="outlined" onClick={openCart}>
                          {t('post.detail.viewInCart')}
                        </Button>
                      ) : (
                        <Button
                          variant="contained"
                          disabled={addToCart.isPending || !user}
                          onClick={() => addToCart.mutate(id)}
                        >
                          {addToCart.isPending
                            ? t('post.detail.adding')
                            : t('post.detail.addToCart')}
                        </Button>
                      )
                    )}
                    {isOwner && (
                      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        {t('post.detail.youOwn')}
                      </Typography>
                    )}
                  </Stack>
                </Stack>
              </Box>
            </Box>
          )}
        </Stack>
      </Container>
    </>
  )
}
