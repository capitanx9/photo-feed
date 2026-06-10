'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter, useParams } from 'next/navigation'
import { Alert, Button, Link as MuiLink, Stack, TextField, Typography } from '@mui/material'
import NextLink from 'next/link'
import { AxiosError } from 'axios'
import { useAuth } from '@/lib/auth/useAuth'
import { registerSchema, type RegisterInput } from '@/lib/auth/schemas'
import { t } from '@/lib/i18n/t'

// Shape of a serializer validation error from DRF: each field maps to a list
// of messages, e.g. { email: ['already exists'], password: ['too short'] }.
type FieldErrors = Record<string, string[]>

export default function RegisterPage() {
  const router = useRouter()
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  const { register: registerUser } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null)
    setFieldErrors({})
    try {
      await registerUser(values)
      router.replace(`/${locale}/login?registered=1`)
    } catch (e) {
      if (e instanceof AxiosError && e.response?.status === 400) {
        setFieldErrors((e.response.data as FieldErrors) ?? {})
      } else {
        setServerError(t('auth.error.unknown'))
      }
    }
  })

  return (
    <Stack spacing={3} component="form" onSubmit={onSubmit} noValidate>
      <Typography variant="h4" component="h1">
        {t('auth.register.heading')}
      </Typography>

      {serverError && <Alert severity="error">{serverError}</Alert>}

      <TextField
        type="email"
        label={t('auth.field.email')}
        autoComplete="email"
        error={!!errors.email || !!fieldErrors.email}
        helperText={errors.email?.message ?? fieldErrors.email?.[0]}
        {...register('email')}
      />
      <TextField
        type="password"
        label={t('auth.field.password')}
        autoComplete="new-password"
        error={!!errors.password || !!fieldErrors.password}
        helperText={errors.password?.message ?? fieldErrors.password?.[0]}
        {...register('password')}
      />

      <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
        {isSubmitting ? t('auth.register.submitting') : t('auth.register.submit')}
      </Button>

      <MuiLink component={NextLink} href={`/${locale}/login`} underline="hover">
        {t('auth.register.toLogin')}
      </MuiLink>
    </Stack>
  )
}
