export const createChatSlice = (set, get) => ({
  aiMessages: [],
  aiMessagesLastUpdated: null,
  isAiTyping: false,
  comboOffer: null,
  isAiConnected: false,
  isAgentOpen: false,
  setIsAgentOpen: (isOpen) => set({ isAgentOpen: isOpen }),
  guestId: Math.floor(Math.random() * 1000000) + 10000,

  connectAgent: () => set({ isAiConnected: true }),
  disconnectAgent: () => set({ isAiConnected: false, isAiTyping: false }),
  clearComboOffer: () => set({ comboOffer: null }),

  _handleChatResponse: (data) => {
    if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
      set(state => ({ 
        aiMessages: [...state.aiMessages, { 
          sender: 'ai', text: data.message, suggested_products: data.suggested_products || []
        }],
        aiMessagesLastUpdated: Date.now(), isAgentOpen: true, isAiTyping: false
      }));
      if (data.combo_offer) set({ comboOffer: data.combo_offer });
      if (data.cart) {
        set({ cart: data.cart.map(item => ({
          id: item.id || item.product_id, name: item.name, price: item.price,
          qty: item.quantity || item.qty, size: item.size, color: item.color, image_url: item.image_url
        }))});
      }
      if (data.ai_discount !== undefined) set({ aiDiscount: data.ai_discount });
    }
  },

  sendAiMessage: async (text) => {
    set(state => ({ 
      aiMessages: [...state.aiMessages, { sender: 'user', text }],
      aiMessagesLastUpdated: Date.now(), isAgentOpen: true, isAiTyping: true
    }));
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/chat/message`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: get().user?.id || get().guestId, text, cart: get().cart })
      });
      get()._handleChatResponse(await res.json());
    } catch(e) {
      console.error("Chat error", e);
      set({ isAiTyping: false });
    }
  },

  sendAiEvent: async (eventName) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/chat/event`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: get().user?.id || get().guestId, event: eventName, cart: get().cart })
      });
      get()._handleChatResponse(await res.json());
    } catch(e) { console.error("Event error", e); }
  }
});
