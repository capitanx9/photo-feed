'use client'

import { useInfiniteQuery, useQuery, type InfiniteData } from '@tanstack/react-query'
import { useAuth } from '@/lib/auth/useAuth'
import { getOrder, listOrders, type PaginatedOrders } from '@/lib/api/orders'

export function useOrders() {
  const { isAuthenticated } = useAuth()
  return useInfiniteQuery<
    PaginatedOrders,
    Error,
    InfiniteData<PaginatedOrders, string | undefined>,
    ['orders'],
    string | undefined
  >({
    queryKey: ['orders'],
    queryFn: ({ pageParam }) => listOrders(pageParam),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.next ?? undefined,
    enabled: isAuthenticated,
  })
}

export function useOrder(id: number) {
  return useQuery({
    queryKey: ['order', id] as const,
    queryFn: () => getOrder(id),
    enabled: Number.isFinite(id),
  })
}
