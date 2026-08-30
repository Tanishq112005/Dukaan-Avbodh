import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// --- Global WebSocket Instance (Outside Store to avoid serialization issues) ---
let socketInstance = null;

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
      activityCount: 0,
      
      trackActivity: () => {
        const { activityCount, sendAiEvent } = get();
        const newCount = activityCount + 1;
        if (newCount >= 5) {
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
      aiMessagesLastUpdated: null,
      isAiTyping: false,
      comboOffer: null,
      isAiConnected: false,
      isAgentOpen: false,
      setIsAgentOpen: (isOpen) => set({ isAgentOpen: isOpen }),
      guestId: Math.floor(Math.random() * 1000000) + 10000, // For users who are not logged in

      connectAgent: () => {
        const { user, guestId } = get();
        if (socketInstance) return; // Already connected

        const connectId = user?.id || guestId;
        socketInstance = new WebSocket(`ws://localhost:8000/ws/chat/${connectId}`);
        
        socketInstance.onopen = () => set({ isAiConnected: true });
        
        socketInstance.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
              set(state => ({ 
                aiMessages: [...state.aiMessages, { sender: 'ai', text: data.message }],
                aiMessagesLastUpdated: Date.now(),
                isAgentOpen: true,
                isAiTyping: false
              }));
              if (data.combo_offer) {
                set({ comboOffer: data.combo_offer });
              }
            }
          } catch (err) { console.error(err) }
        };
        
        socketInstance.onclose = () => {
          set({ isAiConnected: false, isAiTyping: false });
          socketInstance = null;
        };
      },

      disconnectAgent: () => {
        if (socketInstance) {
          const sock = socketInstance;
          socketInstance = null; // Set null FIRST to prevent reconnect race
          sock.onclose = null;  // Remove handler to avoid state update after disconnect
          sock.close();
          set({ isAiConnected: false, isAiTyping: false });
        }
      },

      sendAiMessage: (text) => {
        // Add message to UI immediately
        set(state => ({ 
          aiMessages: [...state.aiMessages, { sender: 'user', text }],
          aiMessagesLastUpdated: Date.now(),
          isAgentOpen: true,
          isAiTyping: true
        }));

        const trySend = () => {
          if (socketInstance && socketInstance.readyState === WebSocket.OPEN) {
            socketInstance.send(text);
          } else if (socketInstance && socketInstance.readyState === WebSocket.CONNECTING) {
            // Socket is still connecting, retry after a short delay
            setTimeout(trySend, 500);
          }
          // If closed/null, silently skip ?" message is still visible in UI
        };
        trySend();
      },

      sendAiEvent: (eventName) => {
        const { cart } = get();
        const trySend = () => {
          if (socketInstance && socketInstance.readyState === WebSocket.OPEN) {
            const payload = { type: 'monitoring_event', event: eventName, cart: cart };
            socketInstance.send(JSON.stringify(payload));
          } else if (socketInstance && socketInstance.readyState === WebSocket.CONNECTING) {
            setTimeout(trySend, 500);
          }
        };
        trySend();
      },
      
      clearComboOffer: () => set({ comboOffer: null })
    }),
    {
      name: 'dukaan-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        cart: state.cart,
        aiMessages: state.aiMessages,
        aiMessagesLastUpdated: state.aiMessagesLastUpdated,
        comboOffer: state.comboOffer,
        isAgentOpen: state.isAgentOpen,
        guestId: state.guestId
      })
    }
  )
)
