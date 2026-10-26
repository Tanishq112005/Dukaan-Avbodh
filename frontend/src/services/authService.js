import apiClient from "./api.js";

/**
 * Authentication and Profile service for Dukaan.
 * Interfaces with Auth/routes:
 *  - /auth/signup
 *  - /auth/login
 *  - /auth/me
 *  - /auth/profile
 *  - /auth/status
 */
export const authService = {
  /**
   * Registers a new user.
   * @param {Object} payload
   * @param {string} payload.name - User's full name
   * @param {string} payload.email - User's email
   * @param {string} payload.password - User's password
   * @param {string} [payload.role="customer"] - "customer" | "merchant"
   * @returns {Promise<{ access_token: string, user_id: number, role: string }>}
   */
  async signup({ name, email, password, role = "customer" }) {
    const res = await apiClient.post("/auth/signup", {
      name,
      email,
      password,
      role,
    });
    return res.data;
  },

  /**
   * Logs in an existing user.
   * @param {Object} payload
   * @param {string} payload.email - User's email
   * @param {string} payload.password - User's password
   * @returns {Promise<{ access_token: string, user_id: number, role: string }>}
   */
  async login({ email, password }) {
    const res = await apiClient.post("/auth/login", {
      email,
      password,
    });
    return res.data;
  },

  /**
   * Fetches currently authenticated user identity based on active Bearer token.
   * @returns {Promise<{ user_id: number, name: string, email: string, role: string, address: string | null }>}
   */
  async getMe() {
    const res = await apiClient.get("/auth/me");
    return res.data;
  },

  /**
   * Fetches user profile by user_id or active Bearer token.
   * @param {number|null} [userId=null]
   * @returns {Promise<{ user_id: number, name: string, email: string, role: string, address: string | null }>}
   */
  async getProfile(userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.get("/auth/profile", config);
    return res.data;
  },

  /**
   * Updates name and/or delivery address for the customer profile.
   * @param {Object} payload
   * @param {string} [payload.name]
   * @param {string} [payload.address]
   * @param {number|null} [userId=null]
   * @returns {Promise<{ user_id: number, name: string, email: string, role: string, address: string | null }>}
   */
  async updateProfile(payload, userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.put("/auth/profile", payload, config);
    return res.data;
  },

  /**
   * Checks whether the current user is an authenticated customer or guest session.
   * @param {number|null} [userId=null]
   * @returns {Promise<{ is_authenticated: boolean, is_guest: boolean, user_id: number | null, name: string | null, role: string | null }>}
   */
  async checkAuthStatus(userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.get("/auth/status", config);
    return res.data;
  },
};

export default authService;
