import { z } from 'zod'

export const PAYMENT_METHODS = ['card', 'paypal', 'crypto', 'cod'] as const

export const checkoutSchema = z.object({
  shipping_name: z.string().min(1, 'Name is required').max(120),
  shipping_address: z.string().min(1, 'Address is required').max(500),
  shipping_city: z.string().min(1, 'City is required').max(120),
  // ZIP can include letters (UK, NL, CA, etc.) and spaces. Just enforce non-empty.
  shipping_zip: z.string().min(1, 'ZIP is required').max(20),
  shipping_country: z.string().max(120),
  payment_method: z.enum(PAYMENT_METHODS),
})

export type CheckoutInput = z.infer<typeof checkoutSchema>
