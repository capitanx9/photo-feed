'use client'

import { useInfiniteQuery, type InfiniteData } from '@tanstack/react-query'
import { listPosts, type PaginatedPosts } from '@/lib/api/posts'

// 3rd generic (`TData`) defaults to `InfiniteData<TQueryFnData>` and the
// `data.pages` accessor depends on that. Spell it out so a future
// refactor doesn't accidentally collapse it back to a single page.
export function useFeed() {
  return useInfiniteQuery<
    PaginatedPosts,
    Error,
    InfiniteData<PaginatedPosts, string | undefined>,
    ['feed'],
    string | undefined
  >({
    queryKey: ['feed'],
    queryFn: ({ pageParam }) => listPosts(pageParam),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.next ?? undefined,
  })
}
