'use client'

import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useParams, useRouter } from 'next/navigation'
import {
  Alert,
  Box,
  Button,
  Container,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { AuthGuard } from '@/lib/auth/AuthGuard'
import { postCreateSchema, type PostCreateInput } from '@/lib/posts/schemas'
import { usePostCreate, type PostCreatePhase } from '@/lib/posts/usePostCreate'
import { t } from '@/lib/i18n/t'

const PHASE_KEY: Record<PostCreatePhase, Parameters<typeof t>[0] | null> = {
  idle: null,
  presigning: 'post.create.phase.presigning',
  uploading: 'post.create.phase.uploading',
  processing: 'post.create.phase.processing',
  creating: 'post.create.phase.creating',
  done: 'post.create.phase.done',
  error: null,
}

export default function NewPostPage() {
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  return (
    <AuthGuard locale={locale}>
      <NewPostForm locale={locale} />
    </AuthGuard>
  )
}

function NewPostForm({ locale }: { locale: string }) {
  const router = useRouter()
  const { phase, error, run } = usePostCreate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    control,
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<PostCreateInput>({
    resolver: zodResolver(postCreateSchema),
    defaultValues: { caption: '', price: '', file: undefined as unknown as File },
  })

  const file = watch('file')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const inFlight = phase !== 'idle' && phase !== 'error' && phase !== 'done'

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null)
    const post = await run({
      file: values.file,
      caption: values.caption,
      price: values.price.trim() === '' ? null : values.price.trim(),
    })
    if (!post) {
      // run() returns null on AbortController abort or after setPhase('error').
      // For 400s from /upload-url/ (bad MIME, oversize) the backend message is
      // already in `error` from usePostCreate. Translate the most common ones.
      if (error) setServerError(error)
      return
    }
    router.replace(`/${locale}/posts/${post.id}`)
  })

  const phaseKey = PHASE_KEY[phase]

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Stack spacing={3} component="form" onSubmit={onSubmit} noValidate>
        <Typography variant="h4" component="h1">
          {t('post.create.heading')}
        </Typography>

        {serverError && <Alert severity="error">{serverError}</Alert>}

        <Box>
          <Button variant="outlined" component="label" disabled={inFlight}>
            {file ? t('post.create.field.fileChange') : t('post.create.field.filePick')}
            <Controller
              control={control}
              name="file"
              render={({ field: { onChange, onBlur, name, ref } }) => (
                <input
                  ref={ref}
                  type="file"
                  name={name}
                  hidden
                  accept="image/jpeg,image/png,image/webp"
                  onBlur={onBlur}
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    onChange(f ?? undefined)
                  }}
                />
              )}
            />
          </Button>
          {file && (
            <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
              {file.name} ({Math.round(file.size / 1024)} KB)
            </Typography>
          )}
          {errors.file && (
            <Typography variant="body2" sx={{ mt: 1, color: 'error.main' }}>
              {errors.file.message}
            </Typography>
          )}
        </Box>

        {previewUrl && (
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
            {/* Local object URL preview — Next/Image can't proxy blob: URLs. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="preview"
              style={{ maxWidth: '100%', maxHeight: 360, objectFit: 'contain' }}
            />
          </Box>
        )}

        <TextField
          label={t('post.create.field.caption')}
          multiline
          minRows={3}
          maxRows={8}
          error={!!errors.caption}
          helperText={errors.caption?.message}
          disabled={inFlight}
          {...register('caption')}
        />

        <TextField
          label={t('post.create.field.price')}
          placeholder="0.00"
          inputMode="decimal"
          error={!!errors.price}
          helperText={errors.price?.message ?? t('post.create.field.priceHint')}
          disabled={inFlight}
          {...register('price')}
        />

        {phaseKey && (
          <Stack spacing={1}>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {t(phaseKey)}
            </Typography>
            <LinearProgress />
          </Stack>
        )}

        {phase === 'error' && error && !serverError && (
          <Alert severity="error" onClose={() => setServerError(null)}>
            {translatePhaseError(error)}
          </Alert>
        )}

        <Button type="submit" variant="contained" size="large" disabled={inFlight}>
          {inFlight ? t('post.create.submitting') : t('post.create.submit')}
        </Button>
      </Stack>
    </Container>
  )
}

function translatePhaseError(raw: string): string {
  if (raw === 'media processing timed out') return t('post.create.error.timeout')
  if (raw === 'media processing failed') return t('post.create.error.processing')
  return raw
}
