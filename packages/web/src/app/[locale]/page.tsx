'use client'

import { useCallback } from 'react'
import { useParams } from 'next/navigation'
import NextLink from 'next/link'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Stack,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import { TopBar } from '@/lib/layout/AppBar'
import { useFeed } from '@/lib/posts/useFeed'
import { useInfiniteSentinel } from '@/lib/posts/useInfiniteSentinel'
import { useAuth } from '@/lib/auth/useAuth'
import { t } from '@/lib/i18n/t'
import type { Post } from '@/lib/api/posts'

export default function FeedPage() {
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  const { isAuthenticated } = useAuth()
  const {
    data,
    error,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useFeed()

  const onIntersect = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const sentinelRef = useInfiniteSentinel(onIntersect, hasNextPage ?? false)

  const posts: Post[] = data?.pages.flatMap((p) => p.results) ?? []

  return (
    <>
      <TopBar locale={locale} />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Stack spacing={3}>
          {!isAuthenticated && (
            <Alert severity="info" icon={false}>
              <Typography variant="body2">
                {t('smoke.anon')}{' '}
                <MuiLink component={NextLink} href={`/${locale}/login`} underline="hover">
                  {t('auth.login.submit')}
                </MuiLink>
              </Typography>
            </Alert>
          )}

          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          )}

          {isError && <Alert severity="error">{error?.message ?? t('feed.loadError')}</Alert>}

          {!isLoading && !isError && posts.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" sx={{ color: 'text.secondary' }}>
                {t('feed.empty')}
              </Typography>
              {isAuthenticated && (
                <Button
                  component={NextLink}
                  href={`/${locale}/posts/new`}
                  variant="contained"
                  sx={{ mt: 2 }}
                >
                  {t('nav.newPost')}
                </Button>
              )}
            </Box>
          )}

          <Stack spacing={4}>
            {posts.map((post) => (
              <PostCard key={post.id} post={post} locale={locale} />
            ))}
          </Stack>

          <Box ref={sentinelRef} sx={{ height: 1 }} />

          {isFetchingNextPage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          )}
        </Stack>
      </Container>
    </>
  )
}

function PostCard({ post, locale }: { post: Post; locale: string }) {
  const imageUrl = post.media[0]?.url
  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        overflow: 'hidden',
        bgcolor: 'background.paper',
      }}
    >
      <MuiLink
        component={NextLink}
        href={`/${locale}/posts/${post.id}`}
        underline="none"
        color="inherit"
      >
        {imageUrl ? (
          <Box sx={{ bgcolor: 'action.hover', display: 'flex', justifyContent: 'center' }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageUrl}
              alt={post.caption || `post ${post.id}`}
              style={{ width: '100%', maxHeight: 600, objectFit: 'contain' }}
            />
          </Box>
        ) : (
          <Box
            sx={{
              bgcolor: 'action.hover',
              height: 240,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {t('feed.mediaPending')}
            </Typography>
          </Box>
        )}
        <Box sx={{ p: 2 }}>
          {post.caption && (
            <Typography variant="body1" sx={{ mb: 1 }}>
              {post.caption}
            </Typography>
          )}
          {post.price && (
            <Typography variant="h6" sx={{ color: 'primary.main' }}>
              ${post.price}
            </Typography>
          )}
        </Box>
      </MuiLink>
    </Box>
  )
}
