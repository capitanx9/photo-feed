import { MUIThemeProvider } from '@/lib/providers/theme'
import { QueryProvider } from '@/lib/providers/query'
import type { ReactNode } from 'react'

// Lab 4 ships 'en' only. Lab 5 makes [locale] real via middleware.
// generateStaticParams pre-renders the en branch at build time so the
// SSR-ed feed doesn't pay for a dynamic-segment cache miss on each hit.
export function generateStaticParams() {
  return [{ locale: 'en' }]
}

export default function LocaleLayout({ children }: { children: ReactNode }) {
  return (
    <MUIThemeProvider>
      <QueryProvider>{children}</QueryProvider>
    </MUIThemeProvider>
  )
}
