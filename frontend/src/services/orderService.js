import apiClient from "./api.js";

/**
 * Service for orders and payments.
 * Interfaces with Order routes (/order/*) and Payment routes (/api/payment/*).
 */
export const orderService = {
  /**
   * Concurrency-locked checkout:
   * Acquires product locks, reserves stock, creates pending order rows,
   * and initializes Razorpay payment order in a single atomic step.
   * @param {Object} payload
   * @param {Array} [payload.items] - Optional list of { product_id, quantity }
   * @param {number} [payload.discount_percentage=0]
   * @param {string} [payload.customer_name]
   * @param {string} [payload.customer_email]
   * @returns {Promise<Object>}
   */
  async checkoutWithLock(payload = {}) {
    const res = await apiClient.post("/order/checkout", payload);
    return res.data;
  },

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
   * @param {Array<number>} [payload.order_ids]
   * @returns {Promise<Object>}
   */
  async createPaymentOrder({ amount, currency = "INR", receipt, order_ids }) {
    const res = await apiClient.post("/api/payment/create-order", {
      amount,
      currency,
      receipt: receipt || `receipt_${Date.now()}`,
      order_ids,
    });
    return res.data;
  },

  /**
   * Verifies Razorpay payment signature on backend.
   * @param {Object} payload
   * @param {string} payload.razorpay_order_id
   * @param {string} payload.razorpay_payment_id
   * @param {string} payload.razorpay_signature
   * @param {Array<number>} [payload.order_ids]
   * @returns {Promise<Object>}
   */
  async verifyPayment(payload) {
    const res = await apiClient.post("/api/payment/verify", payload);
    return res.data;
  },

  /**
   * Polls real-time payment status for a user.
   * @param {number|string} userId
   * @returns {Promise<Object>}
   */
  async checkPaymentStatus(userId) {
    const res = await apiClient.get(`/api/payment/status/${userId}`);
    return res.data;
  },

  /**
   * Cancels an order and releases the reserved stock back to inventory.
   * @param {number} orderId
   * @returns {Promise<Object>}
   */
  async cancelOrder(orderId) {
    const res = await apiClient.post(`/order/cancel/${orderId}`);
    return res.data;
  },
};

export default orderService;
