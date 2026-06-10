'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter, useParams } from 'next/navigation'
import { Alert, Button, Link as MuiLink, Stack, TextField, Typography } from '@mui/material'
import NextLink from 'next/link'
import { AxiosError } from 'axios'
import { useAuth } from '@/lib/auth/useAuth'
import { loginSchema, type LoginInput } from '@/lib/auth/schemas'
import { t } from '@/lib/i18n/t'

export default function LoginPage() {
  const router = useRouter()
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  const { login } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null)
    try {
      await login(values)
      router.replace(`/${locale}`)
    } catch (e) {
      if (e instanceof AxiosError && e.response?.status === 401) {
        setServerError(t('auth.error.invalidCredentials'))
      } else {
        setServerError(t('auth.error.unknown'))
      }
    }
  })

  return (
    <Stack spacing={3} component="form" onSubmit={onSubmit} noValidate>
      <Typography variant="h4" component="h1">
        {t('auth.login.heading')}
      </Typography>

      {serverError && <Alert severity="error">{serverError}</Alert>}

      <TextField
        type="email"
        label={t('auth.field.email')}
        autoComplete="email"
        error={!!errors.email}
        helperText={errors.email?.message}
        {...register('email')}
      />
      <TextField
        type="password"
        label={t('auth.field.password')}
        autoComplete="current-password"
        error={!!errors.password}
        helperText={errors.password?.message}
        {...register('password')}
      />

      <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
        {isSubmitting ? t('auth.login.submitting') : t('auth.login.submit')}
      </Button>

      <MuiLink component={NextLink} href={`/${locale}/register`} underline="hover">
        {t('auth.login.toRegister')}
      </MuiLink>
    </Stack>
  )
}
