'use client'

import { useEffect, useRef } from 'react'

// Generic IntersectionObserver-on-a-ref pattern: attach the returned ref to a
// sentinel element at the bottom of the list. When it scrolls into view,
// `onIntersect` runs (debounced by IO itself — fires once per intersection).
// Caller is responsible for not calling fetchNextPage while one is already
// in flight; useInfiniteQuery exposes isFetchingNextPage for exactly that.
export function useInfiniteSentinel(onIntersect: () => void, enabled: boolean) {
  const ref = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = ref.current
    if (!node || !enabled) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) onIntersect()
      },
      { rootMargin: '200px 0px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [onIntersect, enabled])

  return ref
}
