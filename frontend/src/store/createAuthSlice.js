import { userEventService, EVENT_TYPES } from "../services/userEventService.js";

export const createAuthSlice = (set, get) => ({
  user: null,
  token: null,
  login: (userData, token) => {
    set({ user: userData, token });
    userEventService.trackEvent(EVENT_TYPES.SESSION_START, 0);
    const fetchBackendCart = get().fetchBackendCart;
    if (fetchBackendCart) {
      fetchBackendCart();
    }
    // Directly sync the authenticated user ID and token into AI AgentState
    const syncAiAuth = get().syncAiAuth;
    if (syncAiAuth) {
      syncAiAuth(userData, token, "login");
    }
  },
  logout: () => {
    set({
      user: null,
      token: null,
      cart: [],
      aiDiscount: 0,
      comboOffer: null,
    });
    const startNewChat = get().startNewChat;
    if (startNewChat) {
      startNewChat();
    }
  },
});
