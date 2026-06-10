import { redirect } from 'next/navigation'

// Lab 4 hardcodes 'en'. Lab 5 replaces this with a middleware that
// detects locale from Accept-Language / a cookie.
export default function RootRedirect() {
  redirect('/en')
}
