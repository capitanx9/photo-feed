import { apiClient } from './client'
import type { components } from './schema'

export type Cart = components['schemas']['Cart']
export type CartItem = components['schemas']['CartItem']
export type CartItemAddRequest = components['schemas']['CartItemAddRequest']

export async function getCart(): Promise<Cart> {
  const res = await apiClient.get<Cart>('/api/cart/')
  return res.data
}

export async function addCartItem(payload: CartItemAddRequest): Promise<CartItem> {
  const res = await apiClient.post<CartItem>('/api/cart/items/', payload)
  return res.data
}

export async function updateCartItemQty(id: number, qty: number): Promise<CartItem> {
  const res = await apiClient.patch<CartItem>(`/api/cart/items/${id}/`, { qty })
  return res.data
}

export async function removeCartItem(id: number): Promise<void> {
  await apiClient.delete(`/api/cart/items/${id}/`)
}
