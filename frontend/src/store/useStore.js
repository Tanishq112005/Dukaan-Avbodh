import { create } from 'zustand'

export const useStore = create((set) => ({
  // --- Auth State ---
  user: null,
  token: null,
  login: (userData, token) => set({ user: userData, token }),
  logout: () => set({ user: null, token: null }),

  // --- Product State ---
  products: [],
  setProducts: (products) => set({ products }),
  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),
  selectedType: "",
  setSelectedType: (type) => set({ selectedType: type }),
  maxPrice: 200,
  setMaxPrice: (price) => set({ maxPrice: price }),

  // --- Cart State ---
  cart: [],
  addToCart: (product, qty, size, color) => set((state) => {
    const existing = state.cart.find(item => item.id === product.id && item.size === size && item.color === color)
    if (existing) {
      return {
        cart: state.cart.map(item => 
          (item.id === product.id && item.size === size && item.color === color)
            ? { ...item, qty: item.qty + qty } 
            : item
        )
      }
    }
    return { cart: [...state.cart, { ...product, qty, size, color }] }
  }),
  removeFromCart: (id, size, color) => set((state) => ({
    cart: state.cart.filter(item => !(item.id === id && item.size === size && item.color === color))
  })),
  updateCartQty: (id, size, color, qty) => set((state) => ({
    cart: state.cart.map(item => 
      (item.id === id && item.size === size && item.color === color)
        ? { ...item, qty: Math.max(1, qty) } 
        : item
    )
  })),
  clearCart: () => set({ cart: [] }),
}))
