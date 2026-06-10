import { Box } from '@mui/material'
import type { ReactNode } from 'react'

// Shared shell for /login and /register: centers the form vertically and
// keeps a narrow column on wider viewports.
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 420 }}>{children}</Box>
    </Box>
  )
}
