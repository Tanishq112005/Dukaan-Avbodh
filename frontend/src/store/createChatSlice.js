export const createChatSlice = (set, get) => ({
  aiMessages: [],
  aiMessagesLastUpdated: null,
  isAiTyping: false,
  comboOffer: null,
  isAiConnected: false,
  isAgentOpen: false,
  setIsAgentOpen: (isOpen) => set({ isAgentOpen: isOpen }),
  guestId: Math.floor(Math.random() * 1000000) + 10000,
  pendingPayment: null,
  paymentWatchTimer: null,

  connectAgent: () => set({ isAiConnected: true }),
  disconnectAgent: () => {
    const timer = get().paymentWatchTimer;
    if (timer) clearInterval(timer);
    set({ isAiConnected: false, isAiTyping: false, paymentWatchTimer: null });
  },
  clearComboOffer: () => set({ comboOffer: null }),

  _handleChatResponse: (data) => {
    if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
      const fromText = (data.message || '').match(/https?:\/\/[^\s<>"')\]]+/);
      const payment_link = (data.payment_link && String(data.payment_link).startsWith('http'))
        ? data.payment_link
        : (fromText ? fromText[0] : null);
      set(state => ({ 
        aiMessages: [...state.aiMessages, { 
          sender: 'ai',
          text: data.message,
          suggested_products: data.suggested_products || [],
          payment_link,
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
      if (payment_link && payment_link.startsWith('http') && !get().pendingPayment?.notified) {
        get().watchPayment(payment_link, data.payment_link_id);
      }
    }
  },

  watchPayment: (paymentUrl, paymentLinkId) => {
    const existing = get().paymentWatchTimer;
    if (existing) clearInterval(existing);
    set({ pendingPayment: { url: paymentUrl, id: paymentLinkId || null, notified: false } });
    const timer = setInterval(() => get().pollPaymentStatus(), 4000);
    set({ paymentWatchTimer: timer });
    get().pollPaymentStatus();
  },

  notifyPaymentComplete: () => {
    const pending = get().pendingPayment;
    if (pending?.notified) return;
    const timer = get().paymentWatchTimer;
    if (timer) clearInterval(timer);
    set({
      pendingPayment: { ...(pending || {}), notified: true },
      paymentWatchTimer: null,
    });
    get().sendAiEvent("payment_completed");
  },

  pollPaymentStatus: async () => {
    const pending = get().pendingPayment;
    if (pending?.notified) return;
    const userId = get().user?.id || get().guestId;
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/payment/status/${userId}`);
      const data = await res.json();
      if (data?.paid) {
        get().notifyPaymentComplete();
      }
    } catch (e) {
      console.error("Payment poll failed", e);
    }
  },

  openPaymentLink: (url) => {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
    get().watchPayment(url, get().pendingPayment?.id);
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
    const showTyping = eventName === "payment_completed";
    if (showTyping) set({ isAiTyping: true, isAgentOpen: true });
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/chat/event`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: get().user?.id || get().guestId, event: eventName, cart: get().cart })
      });
      get()._handleChatResponse(await res.json());
    } catch(e) {
      console.error("Event error", e);
      if (showTyping) set({ isAiTyping: false });
    }
  }
});
