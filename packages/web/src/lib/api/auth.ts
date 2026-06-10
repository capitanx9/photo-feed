import { apiClient } from './client'
import type { components } from './schema'

export type User = components['schemas']['User']
type LoginRequest = components['schemas']['LoginRequest']
type RegisterRequest = components['schemas']['RegisterRequest']

export async function register(payload: RegisterRequest): Promise<User> {
  const res = await apiClient.post<User>('/api/auth/register/', payload)
  return res.data
}

export async function login(payload: LoginRequest): Promise<User> {
  const res = await apiClient.post<User>('/api/auth/login/', payload)
  return res.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout/')
}

export async function me(): Promise<User> {
  const res = await apiClient.get<User>('/api/auth/me/')
  return res.data
}

// Used internally by the 401-refresh interceptor.
export async function refresh(): Promise<void> {
  await apiClient.post('/api/auth/refresh/')
}
