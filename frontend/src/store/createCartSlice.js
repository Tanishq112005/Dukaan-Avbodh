export const createCartSlice = (set, get) => ({
  cart: [],
  aiDiscount: 0,
  setAiDiscount: (discount) => set({ aiDiscount: discount }),
  activityCount: 0,
  
  trackActivity: () => {
    const { activityCount, sendAiEvent } = get();
    const newCount = activityCount + 1;
    if (newCount >= 3) {
      if (sendAiEvent) sendAiEvent("activity_threshold_reached");
      set({ activityCount: 0 });
    } else {
      set({ activityCount: newCount });
    }
  },

  addToCart: (product, qty, size, color) => {
    get().trackActivity();
    set((state) => {
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
    });
  },
  
  removeFromCart: (id, size, color) => {
    get().trackActivity();
    set((state) => ({
      cart: state.cart.filter(item => !(item.id === id && item.size === size && item.color === color))
    }));
  },
  
  updateCartQty: (id, size, color, qty) => set((state) => ({
    cart: state.cart.map(item => 
      (item.id === id && item.size === size && item.color === color)
        ? { ...item, qty: Math.max(1, qty) } 
        : item
    )
  })),
  clearCart: () => set({ cart: [] }),
});
