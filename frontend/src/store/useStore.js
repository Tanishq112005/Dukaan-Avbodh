import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Store definition
export const useStore = create(
  persist(
    (set, get) => ({
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
      maxPrice: 3000,
      setMaxPrice: (price) => set({ maxPrice: price }),

      // --- Cart State ---
      cart: [],
      aiDiscount: 0,
      setAiDiscount: (discount) => set({ aiDiscount: discount }),
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

      // --- AI Agent / HTTP State ---
      aiMessages: [],
      aiMessagesLastUpdated: null,
      isAiTyping: false,
      comboOffer: null,
      isAiConnected: false,
      isAgentOpen: false,
      setIsAgentOpen: (isOpen) => set({ isAgentOpen: isOpen }),
      guestId: Math.floor(Math.random() * 1000000) + 10000,

      connectAgent: () => {
        set({ isAiConnected: true });
      },

      disconnectAgent: () => {
        set({ isAiConnected: false, isAiTyping: false });
      },

      sendAiMessage: async (text) => {
        // Add message to UI immediately
        set(state => ({ 
          aiMessages: [...state.aiMessages, { sender: 'user', text }],
          aiMessagesLastUpdated: Date.now(),
          isAgentOpen: true,
          isAiTyping: true
        }));

        const { cart, user, guestId } = get();
        const connectId = user?.id || guestId;
        
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/chat/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: connectId, text: text, cart: cart })
            });
            const data = await res.json();
            
            if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
              set(state => ({ 
                aiMessages: [...state.aiMessages, { 
                  sender: 'ai', 
                  text: data.message,
                  suggested_products: data.suggested_products || []
                }],
                aiMessagesLastUpdated: Date.now(),
                isAgentOpen: true,
                isAiTyping: false
              }));
              if (data.combo_offer) {
                set({ comboOffer: data.combo_offer });
              }
              if (data.cart) {
                const syncedCart = data.cart.map(item => ({
                  id: item.id || item.product_id,
                  name: item.name,
                  price: item.price,
                  qty: item.quantity || item.qty,
                  size: item.size,
                  color: item.color,
                  image_url: item.image_url
                }));
                set({ cart: syncedCart });
              }
              if (data.ai_discount !== undefined) {
                set({ aiDiscount: data.ai_discount });
              }
            }
        } catch(e) {
            console.error("Chat error", e);
            set({ isAiTyping: false });
        }
      },

      sendAiEvent: async (eventName) => {
        const { cart, user, guestId } = get();
        const connectId = user?.id || guestId;
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/chat/event`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: connectId, event: eventName, cart: cart })
            });
            const data = await res.json();
            
            if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
              set(state => ({ 
                aiMessages: [...state.aiMessages, { 
                  sender: 'ai', 
                  text: data.message,
                  suggested_products: data.suggested_products || []
                }],
                aiMessagesLastUpdated: Date.now(),
                isAgentOpen: true,
                isAiTyping: false
              }));
              if (data.combo_offer) {
                set({ comboOffer: data.combo_offer });
              }
              if (data.cart) {
                const syncedCart = data.cart.map(item => ({
                  id: item.id || item.product_id,
                  name: item.name,
                  price: item.price,
                  qty: item.quantity || item.qty,
                  size: item.size,
                  color: item.color,
                  image_url: item.image_url
                }));
                set({ cart: syncedCart });
              }
              if (data.ai_discount !== undefined) {
                set({ aiDiscount: data.ai_discount });
              }
            }
        } catch(e) {
            console.error("Event error", e);
        }
      },
      
      clearComboOffer: () => set({ comboOffer: null })
    }),
    {
      name: 'dukaan-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        cart: state.cart,
        aiDiscount: state.aiDiscount,
        aiMessages: state.aiMessages,
        aiMessagesLastUpdated: state.aiMessagesLastUpdated,
        comboOffer: state.comboOffer,
        isAgentOpen: state.isAgentOpen,
        guestId: state.guestId
      })
    }
  )
)
