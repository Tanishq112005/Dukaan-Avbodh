import apiClient from "./api.js";

/**
 * Authentication service for Dukaan.
 * Interfaces with Auth/routes: /auth/signup and /auth/login.
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
};

export default authService;
