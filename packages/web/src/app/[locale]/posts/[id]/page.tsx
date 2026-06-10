'use client'

import { useParams } from 'next/navigation'
import NextLink from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Link as MuiLink,
  Stack,
  Typography,
} from '@mui/material'
import { getPost } from '@/lib/api/posts'
import { t } from '@/lib/i18n/t'

// Placeholder post-detail page so the post-create redirect lands somewhere
// visible. PR-5 turns this into the real single-post view (with comments,
// add-to-cart, owner controls, etc.).
export default function PostDetailPage() {
  const params = useParams<{ locale: string; id: string }>()
  const locale = params.locale
  const id = Number(params.id)

  const { data: post, isLoading, isError } = useQuery({
    queryKey: ['post', id],
    queryFn: () => getPost(id),
    enabled: Number.isFinite(id),
  })

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Typography variant="h4" component="h1">
          {t('post.detail.heading')}
        </Typography>

        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <CircularProgress />
          </Box>
        )}

        {isError && <Alert severity="error">{t('post.detail.loadError')}</Alert>}

        {post && (
          <Stack spacing={2}>
            {post.media[0]?.url && (
              <Box
                sx={{
                  borderRadius: 1,
                  overflow: 'hidden',
                  border: '1px solid',
                  borderColor: 'divider',
                  display: 'flex',
                  justifyContent: 'center',
                  bgcolor: 'action.hover',
                }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={post.media[0].url}
                  alt={post.caption || `post ${post.id}`}
                  style={{ maxWidth: '100%', maxHeight: 480, objectFit: 'contain' }}
                />
              </Box>
            )}
            {post.caption && <Typography variant="body1">{post.caption}</Typography>}
            {post.price && (
              <Typography variant="h6" sx={{ color: 'primary.main' }}>
                ${post.price}
              </Typography>
            )}
          </Stack>
        )}

        <MuiLink component={NextLink} href={`/${locale}`} underline="hover">
          {t('post.detail.backHome')}
        </MuiLink>
      </Stack>
    </Container>
  )
}
