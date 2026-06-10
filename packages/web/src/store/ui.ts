import { create } from 'zustand'

type UIState = {
  cartOpen: boolean
  openCart: () => void
  closeCart: () => void
}

// UI-only flags. No persist — drawer state should always reset on reload.
export const useUIStore = create<UIState>((set) => ({
  cartOpen: false,
  openCart: () => set({ cartOpen: true }),
  closeCart: () => set({ cartOpen: false }),
}))
