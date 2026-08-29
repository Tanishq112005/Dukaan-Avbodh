import { create } from 'zustand'

export const useStore = create((set, get) => ({
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
  activityCount: 0,
  
  trackActivity: () => {
    const { activityCount, sendAiEvent } = get();
    const newCount = activityCount + 1;
    if (newCount >= 3) {
      sendAiEvent("activity_threshold_reached");
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

  // --- AI Agent / WebSocket State ---
  aiMessages: [],
  comboOffer: null,
  isAiConnected: false,
  ws: null,

  connectAgent: () => {
    const { user, ws } = get();
    if (!user || !user.id || ws) return;

    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${user.id}`);
    
    socket.onopen = () => set({ isAiConnected: true, ws: socket });
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
          set(state => ({ aiMessages: [...state.aiMessages, { sender: 'ai', text: data.message }] }));
          if (data.combo_offer) {
            set({ comboOffer: data.combo_offer });
          }
        }
      } catch (err) { console.error(err) }
    };
    
    socket.onclose = () => set({ isAiConnected: false, ws: null });
  },

  disconnectAgent: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null, isAiConnected: false, aiMessages: [], comboOffer: null });
    }
  },

  sendAiMessage: (text) => {
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(text);
      set(state => ({ aiMessages: [...state.aiMessages, { sender: 'user', text }] }));
    }
  },

  sendAiEvent: (eventName) => {
    const { ws, cart } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      const payload = { type: 'monitoring_event', event: eventName, cart: cart };
      ws.send(JSON.stringify(payload));
    }
  },
  
  clearComboOffer: () => set({ comboOffer: null })
}))
