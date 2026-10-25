import { userEventService, EVENT_TYPES } from "../services/userEventService";

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
  },
  logout: () => {
    set({
      user: null,
      token: null,
      cart: [],
      aiDiscount: 0,
      comboOffer: null,
    });
  },
});
