import { agentService } from "../services/agentService.js";
import { userEventService, EVENT_TYPES } from "../services/userEventService.js";

const generateUUID = () => {
  if (typeof window !== "undefined" && window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return "thread_" + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
};

const normalizeProducts = (items) => {
  if (!Array.isArray(items)) return [];
  return items.map((item) => {
    if (!item) return item;
    const p = item.product && typeof item.product === "object"
      ? { ...item.product, id: item.product.id || item.product_id }
      : item;
    const prodId = p.id || p.product_id;
    return {
      ...p,
      id: prodId,
      name: p.name || "Product",
      price: p.price !== undefined && p.price !== null ? p.price : 0,
      image_url: p.image_url || p.image || null,
    };
  });
};

export const createChatSlice = (set, get) => ({
  aiMessages: [],
  aiMessagesLastUpdated: null,
  isAiTyping: false,
  comboOffer: null,
  isAiConnected: false,
  isAgentOpen: false,
  thread_id: generateUUID(),
  get threadId() {
    return this.thread_id;
  },
  setIsAgentOpen: (isOpen) => set({ isAgentOpen: isOpen }),
  guestId: Math.floor(Math.random() * 1000000) + 10000,
  pendingPayment: null,
  paymentWatchTimer: null,

  startNewChat: () => {
    const timer = get().paymentWatchTimer;
    if (timer) clearInterval(timer);
    const newThread = generateUUID();
    set({
      aiMessages: [],
      thread_id: newThread,
      comboOffer: null,
      pendingPayment: null,
      paymentWatchTimer: null,
    });
  },

  connectAgent: () => set({ isAiConnected: true }),
  disconnectAgent: () => {
    const timer = get().paymentWatchTimer;
    if (timer) clearInterval(timer);
    set({ isAiConnected: false, isAiTyping: false, paymentWatchTimer: null });
  },
  clearComboOffer: () => set({ comboOffer: null }),

  _handleChatResponse: (data) => {
    if (!data) return;

    if (data.type === "chat_reply" || data.type === "proactive_suggestion") {
      const fromText = (data.message || "").match(/https?:\/\/[^\s<>"')\]]+/);
      const payment_link =
        data.payment_link && String(data.payment_link).startsWith("http")
          ? data.payment_link
          : fromText
          ? fromText[0]
          : null;

      set((state) => ({
        aiMessages: [
          ...state.aiMessages,
          {
            sender: "ai",
            text: data.message,
            suggested_products: normalizeProducts(data.suggested_products),
            payment_link,
          },
        ],
        aiMessagesLastUpdated: Date.now(),
        isAgentOpen: true,
        isAiTyping: false,
      }));

      if (data.combo_offer) set({ comboOffer: data.combo_offer });

      if (data.cart && Array.isArray(data.cart)) {
        set({
          cart: data.cart.map((item) => ({
            id: item.id || item.product_id,
            name: item.name,
            price: item.price,
            qty: item.quantity || item.qty || 1,
            size: item.size || null,
            color: item.color || null,
            image_url: item.image_url,
          })),
        });
      }

      if (data.ai_discount !== undefined) {
        set({ aiDiscount: Number(data.ai_discount) });
      }

      if (payment_link && payment_link.startsWith("http") && !get().pendingPayment?.notified) {
        get().watchPayment(payment_link, data.payment_link_id);
      }
    }
  },

  watchPayment: (paymentUrl, paymentLinkId) => {
    const existing = get().paymentWatchTimer;
    if (existing) clearInterval(existing);
    set({
      pendingPayment: { url: paymentUrl, id: paymentLinkId || null, notified: false },
    });
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
    if (!pending || pending?.notified) return;
    const userId = get().user?.id || get().guestId;
    try {
      const baseUrl = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://localhost:8000";
      const res = await fetch(
        `${baseUrl}/api/payment/status/${userId}`
      );
      const data = await res.json();
      if (data?.paid) {
        get().notifyPaymentComplete();
      }
    } catch (e) {
      console.debug("[PaymentStatus] Poll checked:", e);
    }
  },

  openPaymentLink: (url) => {
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
    get().watchPayment(url, get().pendingPayment?.id);
  },

  sendAiMessage: async (text) => {
    if (!text || !text.trim()) return;

    const userMessage = { sender: "user", text };
    const streamingAiMessage = {
      sender: "ai",
      text: "",
      isStreaming: true,
      streamingStatus: "Consulting stylist...",
      suggested_products: [],
    };

    set((state) => ({
      aiMessages: [...state.aiMessages, userMessage, streamingAiMessage],
      aiMessagesLastUpdated: Date.now(),
      isAgentOpen: true,
      isAiTyping: true,
    }));

    const userId = get().user?.id || get().guestId;
    const threadId = get().thread_id || get().threadId;
    const cart = get().cart || [];

    let accumulatedText = "";

    try {
      await agentService.streamUserMessage(
        { userId, threadId, text, cart },
        {
          onToken: (token) => {
            accumulatedText += token;
            set((state) => {
              const msgs = [...state.aiMessages];
              const lastIdx = msgs.length - 1;
              const last = msgs[lastIdx];
              if (last && last.sender === "ai") {
                msgs[lastIdx] = {
                  ...last,
                  text: accumulatedText,
                  isStreaming: true,
                  streamingStatus: null,
                };
              }
              return { aiMessages: msgs, isAiTyping: false };
            });
          },
          onNodeUpdate: (nodeName) => {
            const statusMap = {
              director: "Analyzing look and style...",
              general: "Finding atelier recommendations...",
              catalog: "Checking inventory...",
              negotiation: "Calculating VIP discount...",
              cart: "Updating shopping bag...",
              post_process: "Finalizing recommendations...",
            };
            const label = statusMap[nodeName] || "Stylist is thinking...";
            set((state) => {
              const msgs = [...state.aiMessages];
              const lastIdx = msgs.length - 1;
              const last = msgs[lastIdx];
              if (last && last.sender === "ai" && !last.text) {
                msgs[lastIdx] = {
                  ...last,
                  streamingStatus: label,
                };
              }
              return { aiMessages: msgs };
            });
          },
          onComplete: (payload) => {
            set((state) => {
              const msgs = [...state.aiMessages];
              const lastIdx = msgs.length - 1;
              const last = msgs[lastIdx];
              if (last && last.sender === "ai") {
                msgs[lastIdx] = {
                  ...last,
                  text: payload.message || accumulatedText || "Sorry, I couldn't process that. Please try again.",
                  isStreaming: false,
                  streamingStatus: null,
                  suggested_products: normalizeProducts(payload.suggested_products),
                  payment_link: payload.payment_link || null,
                };
              }
              return { aiMessages: msgs, isAiTyping: false };
            });

            if (payload.combo_offer) set({ comboOffer: payload.combo_offer });
            if (payload.cart && Array.isArray(payload.cart)) {
              set({
                cart: payload.cart.map((item) => ({
                  id: item.id || item.product_id,
                  name: item.name,
                  price: item.price,
                  qty: item.quantity || item.qty || 1,
                  size: item.size || null,
                  color: item.color || null,
                  image_url: item.image_url,
                })),
              });
            }
            if (payload.ai_discount !== undefined) {
              set({ aiDiscount: Number(payload.ai_discount) });
            }
            if (
              payload.payment_link &&
              String(payload.payment_link).startsWith("http") &&
              !get().pendingPayment?.notified
            ) {
              get().watchPayment(payload.payment_link, payload.payment_link_id);
            }
          },
        }
      );
    } catch (streamErr) {
      console.warn("[AgentWidget] Stream error, falling back to standard JSON endpoint:", streamErr);
      try {
        const responseData = await agentService.sendUserMessage({
          userId,
          threadId,
          text,
          cart,
        });
        set((state) => {
          const msgs = [...state.aiMessages];
          if (msgs.length > 0 && msgs[msgs.length - 1].sender === "ai") {
            msgs.pop();
          }
          return { aiMessages: msgs };
        });
        get()._handleChatResponse(responseData);
      } catch (err) {
        console.error("[AgentWidget] Both stream and fallback failed:", err);
        set((state) => {
          const msgs = [...state.aiMessages];
          if (msgs.length > 0 && msgs[msgs.length - 1].sender === "ai") {
            msgs[msgs.length - 1] = {
              sender: "ai",
              text: "I'm having a brief connection delay. Please feel free to ask again in a moment.",
              isStreaming: false,
              streamingStatus: null,
            };
          }
          return { aiMessages: msgs, isAiTyping: false };
        });
      }
    }
  },

  sendAiEvent: async (eventName, payload = {}) => {
    const showTyping = eventName === "payment_completed" || eventName === "viewed_checkout";
    if (showTyping) set({ isAiTyping: true, isAgentOpen: true });

    try {
      const userId = get().user?.id || get().guestId;
      const threadId = get().thread_id || get().threadId;
      const cart = get().cart || [];

      const responseData = await agentService.sendUserEvent({
        userId,
        threadId,
        event: eventName,
        cart,
        ...payload,
      });

      get()._handleChatResponse(responseData);
    } catch (e) {
      console.debug("[AgentWidget] Proactive event processed:", e);
      if (showTyping) set({ isAiTyping: false });
    }
  },

  acceptSuggestion: (product) => {
    if (!product) return;
    userEventService.trackEvent(EVENT_TYPES.SUGGESTION_ACCEPTED, product.id);
    get().addToCart(product, 1, product.sizes?.split(",")[0]?.trim() || "M", "Default");
    get().sendAiMessage(`I'd love to take ${product.name}!`);
  },

  skipSuggestion: (product) => {
    if (product) {
      userEventService.trackEvent(EVENT_TYPES.SUGGESTION_SKIPPED, product.id);
    }
    get().sendAiEvent("combo_declined");
  },
});
