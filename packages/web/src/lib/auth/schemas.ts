import { z } from 'zod'

// Mirror of the Django validators. Email is required + valid. Password
// only enforces non-empty here; Django's validate_password runs the
// full policy (length, common-passwords blocklist) server-side, and the
// 400 response is surfaced inline. Per the plan, complex-password rules
// are deliberately off — `pass1234` works.
export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, 'Password is required'),
})

export type LoginInput = z.infer<typeof loginSchema>

export const registerSchema = loginSchema
export type RegisterInput = z.infer<typeof registerSchema>
