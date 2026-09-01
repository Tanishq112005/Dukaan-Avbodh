export const createAuthSlice = (set) => ({
  user: null,
  token: null,
  login: (userData, token) => set({ user: userData, token }),
  logout: () => set({ user: null, token: null }),
});
