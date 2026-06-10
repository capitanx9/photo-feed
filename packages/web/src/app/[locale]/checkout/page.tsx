'use client'

import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useParams, useRouter } from 'next/navigation'
import NextLink from 'next/link'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  FormControlLabel,
  FormLabel,
  Grid,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
  Link as MuiLink,
} from '@mui/material'
import { TopBar } from '@/lib/layout/AppBar'
import { AuthGuard } from '@/lib/auth/AuthGuard'
import { useCart } from '@/lib/cart/useCart'
import { checkout } from '@/lib/api/orders'
import {
  checkoutSchema,
  PAYMENT_METHODS,
  type CheckoutInput,
} from '@/lib/orders/schemas'
import { t } from '@/lib/i18n/t'

const PAYMENT_LABEL_KEY = {
  card: 'checkout.payment.card',
  paypal: 'checkout.payment.paypal',
  crypto: 'checkout.payment.crypto',
  cod: 'checkout.payment.cod',
} as const

export default function CheckoutPage() {
  const params = useParams<{ locale: string }>()
  const locale = params.locale
  return (
    <>
      <TopBar locale={locale} />
      <AuthGuard locale={locale}>
        <CheckoutContent locale={locale} />
      </AuthGuard>
    </>
  )
}

function CheckoutContent({ locale }: { locale: string }) {
  const router = useRouter()
  const qc = useQueryClient()
  const { data: cart, isLoading: cartLoading } = useCart()
  const [serverError, setServerError] = useState<string | null>(null)

  const { control, register, handleSubmit, formState: { errors } } = useForm<CheckoutInput>({
    resolver: zodResolver(checkoutSchema),
    defaultValues: {
      shipping_name: '',
      shipping_address: '',
      shipping_city: '',
      shipping_zip: '',
      shipping_country: '',
      payment_method: 'card',
    },
  })

  const checkoutMutation = useMutation({
    mutationFn: checkout,
    onSuccess: (order) => {
      void qc.invalidateQueries({ queryKey: ['cart'] })
      router.replace(`/${locale}/orders/${order.id}`)
    },
  })

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null)
    try {
      await checkoutMutation.mutateAsync(values)
    } catch (e) {
      if (e instanceof AxiosError) {
        const detail = (e.response?.data as { detail?: string } | undefined)?.detail
        setServerError(detail ?? t('checkout.error.generic'))
      } else {
        setServerError(t('checkout.error.generic'))
      }
    }
  })

  const isEmpty = !cartLoading && (!cart || cart.items.length === 0)

  if (cartLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 6, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    )
  }

  if (isEmpty) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, textAlign: 'center' }}>
        <Stack spacing={2}>
          <Typography variant="h5">{t('checkout.empty')}</Typography>
          <MuiLink component={NextLink} href={`/${locale}`} underline="hover">
            {t('post.detail.backHome')}
          </MuiLink>
        </Stack>
      </Container>
    )
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        {t('checkout.heading')}
      </Typography>

      <Grid container spacing={4} component="form" onSubmit={onSubmit} noValidate>
        <Grid size={{ xs: 12, md: 7 }}>
          <Stack spacing={3}>
            {serverError && <Alert severity="error">{serverError}</Alert>}

            <Typography variant="h6">{t('checkout.section.shipping')}</Typography>

            <TextField
              label={t('checkout.field.name')}
              autoComplete="name"
              error={!!errors.shipping_name}
              helperText={errors.shipping_name?.message}
              disabled={checkoutMutation.isPending}
              {...register('shipping_name')}
            />

            <TextField
              label={t('checkout.field.address')}
              autoComplete="street-address"
              multiline
              minRows={2}
              error={!!errors.shipping_address}
              helperText={errors.shipping_address?.message}
              disabled={checkoutMutation.isPending}
              {...register('shipping_address')}
            />

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField
                label={t('checkout.field.city')}
                autoComplete="address-level2"
                fullWidth
                error={!!errors.shipping_city}
                helperText={errors.shipping_city?.message}
                disabled={checkoutMutation.isPending}
                {...register('shipping_city')}
              />
              <TextField
                label={t('checkout.field.zip')}
                autoComplete="postal-code"
                fullWidth
                error={!!errors.shipping_zip}
                helperText={errors.shipping_zip?.message}
                disabled={checkoutMutation.isPending}
                {...register('shipping_zip')}
              />
            </Stack>

            <TextField
              label={t('checkout.field.country')}
              autoComplete="country-name"
              error={!!errors.shipping_country}
              helperText={errors.shipping_country?.message}
              disabled={checkoutMutation.isPending}
              {...register('shipping_country')}
            />

            <Divider />
            <Typography variant="h6">{t('checkout.section.payment')}</Typography>

            <Controller
              control={control}
              name="payment_method"
              render={({ field }) => (
                <FormControl error={!!errors.payment_method}>
                  <FormLabel id="payment-method-label">
                    {t('checkout.field.paymentMethod')}
                  </FormLabel>
                  <RadioGroup
                    aria-labelledby="payment-method-label"
                    value={field.value}
                    onChange={(_, v) => field.onChange(v)}
                  >
                    {PAYMENT_METHODS.map((m) => (
                      <FormControlLabel
                        key={m}
                        value={m}
                        control={<Radio disabled={checkoutMutation.isPending} />}
                        label={t(PAYMENT_LABEL_KEY[m])}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              )}
            />

            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={checkoutMutation.isPending}
            >
              {checkoutMutation.isPending
                ? t('checkout.submitting')
                : t('checkout.submit')}
            </Button>
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
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
              {t('checkout.section.summary')}
            </Typography>
            <Stack spacing={1}>
              {cart!.items.map((it) => (
                <Stack
                  key={it.id}
                  direction="row"
                  sx={{ alignItems: 'baseline', justifyContent: 'space-between' }}
                >
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {t('checkout.line', { id: it.post_id, qty: it.qty })}
                  </Typography>
                  <Typography variant="body2">
                    ${(Number(it.price) * it.qty).toFixed(2)}
                  </Typography>
                </Stack>
              ))}
            </Stack>
            <Divider sx={{ my: 2 }} />
            <Stack direction="row" sx={{ justifyContent: 'space-between' }}>
              <Typography variant="subtitle1">{t('cart.total')}</Typography>
              <Typography variant="h6">${cart!.total}</Typography>
            </Stack>
          </Box>
        </Grid>
      </Grid>
    </Container>
  )
}
