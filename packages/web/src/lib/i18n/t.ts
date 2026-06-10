import en from '@/messages/en.json'

// L5-prep-2: thin wrapper so every UI string is a t(key) call from day one.
// Lab 4 looks up en.json synchronously, with optional {placeholder} interpolation.
// Lab 5 swaps this for next-intl's useTranslations() — no JSX changes needed.
export function t(key: keyof typeof en, params?: Record<string, string | number>): string {
  let s: string = en[key]
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      s = s.replace(`{${k}}`, String(v))
    }
  }
  return s
}
