'use client'

import { CssBaseline } from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import { AppRouterCacheProvider } from '@mui/material-nextjs/v16-appRouter'
import type { ReactNode } from 'react'

// Minimal theme for PR-1. Real palette/typography work lands later when
// pages actually need it. We hand emotion the Geist CSS variable from
// app/layout.tsx so MUI components inherit the same font as the body.
const theme = createTheme({
  cssVariables: true,
  typography: {
    fontFamily: 'var(--font-geist-sans), Arial, Helvetica, sans-serif',
  },
})

export function MUIThemeProvider({ children }: { children: ReactNode }) {
  return (
    <AppRouterCacheProvider options={{ enableCssLayer: true }}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AppRouterCacheProvider>
  )
}
