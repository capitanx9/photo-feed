import { apiClient } from './client'
import type { components } from './schema'

export type Order = components['schemas']['Order']
export type OrderItem = components['schemas']['OrderItem']
export type CheckoutRequest = components['schemas']['CheckoutRequest']
export type PaymentMethod = components['schemas']['PaymentMethodEnum']
export type PaginatedOrders = components['schemas']['PaginatedOrderList']

export async function checkout(payload: CheckoutRequest): Promise<Order> {
  const res = await apiClient.post<Order>('/api/orders/checkout/', payload)
  return res.data
}

export async function listOrders(pageUrl?: string): Promise<PaginatedOrders> {
  const url = pageUrl ?? '/api/orders/'
  const res = await apiClient.get<PaginatedOrders>(url)
  return res.data
}

export async function getOrder(id: number): Promise<Order> {
  const res = await apiClient.get<Order>(`/api/orders/${id}/`)
  return res.data
}
