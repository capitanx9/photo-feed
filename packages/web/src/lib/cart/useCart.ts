'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/lib/auth/useAuth'
import {
  addCartItem,
  getCart,
  removeCartItem,
  updateCartItemQty,
  type Cart,
  type CartItem,
} from '@/lib/api/cart'

const KEY = ['cart'] as const

export function useCart() {
  const { isAuthenticated } = useAuth()
  return useQuery({
    queryKey: KEY,
    queryFn: getCart,
    enabled: isAuthenticated,
    staleTime: 10_000,
  })
}

function recomputeTotal(items: CartItem[]): string {
  // Server stores total as a string; mirror that. Optimistic recompute is
  // best-effort — server-truth lands on invalidation and overwrites this.
  const sum = items.reduce((acc, it) => acc + Number(it.price) * it.qty, 0)
  return sum.toFixed(2)
}

export function useAddToCart() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (postId: number) => addCartItem({ post_id: postId, qty: 1 }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: KEY })
    },
  })
}

export function useUpdateCartItemQty() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, qty }: { id: number; qty: number }) => updateCartItemQty(id, qty),
    onMutate: async ({ id, qty }) => {
      await qc.cancelQueries({ queryKey: KEY })
      const prev = qc.getQueryData<Cart>(KEY)
      if (prev) {
        const items = prev.items.map((it) => (it.id === id ? { ...it, qty } : it))
        qc.setQueryData<Cart>(KEY, { ...prev, items, total: recomputeTotal(items) })
      }
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev)
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: KEY })
    },
  })
}

export function useRemoveCartItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => removeCartItem(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: KEY })
      const prev = qc.getQueryData<Cart>(KEY)
      if (prev) {
        const items = prev.items.filter((it) => it.id !== id)
        qc.setQueryData<Cart>(KEY, { ...prev, items, total: recomputeTotal(items) })
      }
      return { prev }
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev)
    },
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: KEY })
    },
  })
}
