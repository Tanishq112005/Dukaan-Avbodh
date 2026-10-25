export const createAuthSlice = (set, get) => ({
  user: null,
  token: null,
  login: (userData, token) => {
    set({ user: userData, token });
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
