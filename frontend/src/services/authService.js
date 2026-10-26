import apiClient from "./api.js";

/**
 * Authentication and Profile service for Dukaan.
 * Interfaces with Auth/routes:
 *  - /auth/signup/request-otp
 *  - /auth/signup/verify-otp
 *  - /auth/signup/resend-otp
 *  - /auth/forgot-password/request-otp
 *  - /auth/forgot-password/verify-otp
 *  - /auth/forgot-password/reset-password
 *  - /auth/signup (legacy direct)
 *  - /auth/login
 *  - /auth/me
 *  - /auth/profile
 *  - /auth/status
 */
export const authService = {
  /**
   * Requests a 6-digit email verification OTP for signup (5-min TTL).
   * @param {Object} payload
   * @param {string} payload.name - User's full name
   * @param {string} payload.email - User's email
   * @param {string} payload.password - User's password
   * @param {string} [payload.role="customer"] - "customer" | "merchant"
   * @param {string} [payload.address=""] - Delivery address
   * @param {string|null} [payload.thread_id=null] - Active conversation thread
   * @returns {Promise<{ success: boolean, message: string, email: string }>}
   */
  async requestSignupOtp({ name, email, password, role = "customer", address = "", thread_id = null }) {
    const res = await apiClient.post("/auth/signup/request-otp", {
      name,
      email,
      password,
      role,
      address,
      thread_id,
    });
    return res.data;
  },

  /**
   * Verifies the 6-digit signup OTP from Redis and creates the account.
   * @param {Object} payload
   * @param {string} payload.email - User's email
   * @param {string} payload.otp - 6-digit numeric OTP code
   * @returns {Promise<{ success: boolean, access_token: string, user_id: number, role: string, name?: string, email?: string, address?: string }>}
   */
  async verifySignupOtp({ email, otp }) {
    const res = await apiClient.post("/auth/signup/verify-otp", {
      email,
      otp,
    });
    return res.data;
  },

  /**
   * Resends a fresh 6-digit verification code with 5-minute TTL.
   * @param {Object} payload
   * @param {string} payload.email - User's email
   * @returns {Promise<{ success: boolean, message: string, email: string }>}
   */
  async resendSignupOtp({ email }) {
    const res = await apiClient.post("/auth/signup/resend-otp", {
      email,
    });
    return res.data;
  },

  /**
   * Initiates password reset by sending a 6-digit OTP to user email.
   * @param {Object} payload
   * @param {string} payload.email - User's registered email
   * @returns {Promise<{ success: boolean, message: string, email: string }>}
   */
  async requestForgotPasswordOtp({ email }) {
    const res = await apiClient.post("/auth/forgot-password/request-otp", {
      email,
    });
    return res.data;
  },

  /**
   * Verifies the 6-digit password reset OTP and receives a reset authorization token.
   * @param {Object} payload
   * @param {string} payload.email - User's email
   * @param {string} payload.otp - 6-digit OTP code
   * @returns {Promise<{ success: boolean, message: string, reset_token: string, email: string }>}
   */
  async verifyForgotPasswordOtp({ email, otp }) {
    const res = await apiClient.post("/auth/forgot-password/verify-otp", {
      email,
      otp,
    });
    return res.data;
  },

  /**
   * Resets account password using the verified reset authorization token.
   * @param {Object} payload
   * @param {string} payload.email - User's email
   * @param {string} payload.new_password - New password
   * @param {string} [payload.reset_token] - Reset authorization token
   * @param {string} [payload.otp] - Optional direct OTP code
   * @returns {Promise<{ success: boolean, message: string }>}
   */
  async resetPassword({ email, new_password, reset_token = null, otp = null }) {
    const res = await apiClient.post("/auth/forgot-password/reset-password", {
      email,
      new_password,
      reset_token,
      otp,
    });
    return res.data;
  },

  /**
   * Registers a new user directly (backward compatible).
   * @param {Object} payload
   */
  async signup({ name, email, password, role = "customer", address = "", thread_id = null }) {
    const res = await apiClient.post("/auth/signup", {
      name,
      email,
      password,
      role,
      address,
      thread_id,
    });
    return res.data;
  },

  /**
   * Logs in an existing user.
   */
  async login({ email, password, thread_id = null }) {
    const res = await apiClient.post("/auth/login", {
      email,
      password,
      thread_id,
    });
    return res.data;
  },

  /**
   * Fetches currently authenticated user identity based on active Bearer token.
   */
  async getMe() {
    const res = await apiClient.get("/auth/me");
    return res.data;
  },

  /**
   * Fetches user profile by user_id or active Bearer token.
   */
  async getProfile(userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.get("/auth/profile", config);
    return res.data;
  },

  /**
   * Updates name and/or delivery address for the customer profile.
   */
  async updateProfile(payload, userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.put("/auth/profile", payload, config);
    return res.data;
  },

  /**
   * Checks whether the current user is an authenticated customer or guest session.
   */
  async checkAuthStatus(userId = null) {
    const config = userId ? { params: { user_id: userId } } : {};
    const res = await apiClient.get("/auth/status", config);
    return res.data;
  },
};

export default authService;
