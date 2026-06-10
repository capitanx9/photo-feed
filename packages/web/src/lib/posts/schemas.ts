import { z } from 'zod'

const MAX_FILE_BYTES = 10 * 1024 * 1024
const ALLOWED_MIME = ['image/jpeg', 'image/png', 'image/webp']

// Backend's DecimalField(max_digits=10, decimal_places=2): up to 8 integer
// digits + optional ".dd". Accept blank — translated to null before submit.
const priceRegex = /^\d{1,8}(\.\d{1,2})?$/

export const postCreateSchema = z.object({
  caption: z.string().max(2000),
  price: z
    .string()
    .trim()
    .refine((v) => v === '' || priceRegex.test(v), {
      message: 'Price must be a number with up to 2 decimal places',
    }),
  file: z
    .instanceof(File, { message: 'Pick an image' })
    .refine((f) => ALLOWED_MIME.includes(f.type), {
      message: 'Only JPEG, PNG, or WebP images are allowed',
    })
    .refine((f) => f.size <= MAX_FILE_BYTES, {
      message: 'Image must be 10 MB or smaller',
    }),
})

export type PostCreateInput = z.infer<typeof postCreateSchema>
