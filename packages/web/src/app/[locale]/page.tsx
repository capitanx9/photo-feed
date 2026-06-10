'use client'

import { Box, Container, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
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
  const { data, isLoading, isError } = useHealth()

  const status = isLoading
    ? t('smoke.health.checking')
    : isError
      ? t('smoke.health.error')
      : data?.ok
        ? t('smoke.health.ok')
        : t('smoke.health.error')

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Stack spacing={2}>
        <Typography variant="h3" component="h1">
          {t('smoke.heading')}
        </Typography>
        <Box>
          <Typography variant="body1">{status}</Typography>
        </Box>
      </Stack>
    </Container>
  )
}
