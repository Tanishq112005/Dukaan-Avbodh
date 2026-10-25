import apiClient from "./api.js";

/**
 * Service for orders and payments.
 * Interfaces with Order/routes (/order/*) and Payment routes (/api/payment/*).
 */
export const orderService = {
  /**
   * Creates an order for the authenticated user from their active cart.
   * @returns {Promise<Object>}
   */
  async createOrder() {
    const res = await apiClient.post("/order/create");
    return res.data;
  },

  /**
   * Retrieves all orders for the authenticated user.
   * @returns {Promise<Array>}
   */
  async getUserOrders() {
    const res = await apiClient.get("/order/get");
    return res.data.orders || res.data || [];
  },

  /**
   * Creates a Razorpay payment order.
   * @param {Object} payload
   * @param {number} payload.amount - Amount in paise (e.g. 100 paise = 1 INR)
   * @param {string} [payload.currency="INR"]
   * @param {string} [payload.receipt]
   * @returns {Promise<Object>}
   */
  async createPaymentOrder({ amount, currency = "INR", receipt }) {
    const res = await apiClient.post("/api/payment/create-order", {
      amount,
      currency,
      receipt: receipt || `receipt_${Date.now()}`,
    });
    return res.data;
  },

  /**
   * Verifies Razorpay payment signature on backend.
   * @param {Object} payload
   * @param {string} payload.razorpay_order_id
   * @param {string} payload.razorpay_payment_id
   * @param {string} payload.razorpay_signature
   * @returns {Promise<Object>}
   */
  async verifyPayment(payload) {
    const res = await apiClient.post("/api/payment/verify", payload);
    return res.data;
  },
};

export default orderService;
