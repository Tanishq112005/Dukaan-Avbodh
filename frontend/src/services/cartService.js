import apiClient from "./api.js";

/**
 * Service for managing the user's shopping cart.
 * Interfaces with Cart/routes: /cart/*
 */
export const cartService = {
  /**
   * Fetches cart items for the authenticated user from the database.
   * @returns {Promise<Array>}
   */
  async getCartItems() {
    const res = await apiClient.get("/cart/items");
    return res.data.cart_items || res.data.items || res.data || [];
  },

  /**
   * Fetches cart summary calculation from the backend.
   * @returns {Promise<Object>}
   */
  async getCartSummary() {
    const res = await apiClient.get("/cart/summary");
    return res.data;
  },

  /**
   * Adds an item to the user's persistent backend cart.
   * @param {Object} item
   * @param {number} item.productId
   * @param {number} [item.quantity=1]
   * @param {string|null} [item.size=null]
   * @returns {Promise<Object>}
   */
  async addItem({ productId, quantity = 1, size = null, discount_percentage = 0, discounted_price = null }) {
    const res = await apiClient.post("/cart/add", {
      product_id: Number(productId),
      quantity: Number(quantity),
      size: size || null,
      discount_percentage: Number(discount_percentage || 0),
      discounted_price: discounted_price !== null && discounted_price !== undefined ? Number(discounted_price) : null,
    });
    return res.data;
  },

  async updateItemDiscount({ productId, discountPercentage, discountedPrice = null, size = null }) {
    const res = await apiClient.patch("/cart/item/discount", {
      product_id: Number(productId),
      discount_percentage: Number(discountPercentage),
      discounted_price: discountedPrice !== null && discountedPrice !== undefined ? Number(discountedPrice) : null,
      size: size || null,
    });
    return res.data;
  },

  /**
   * Updates an item's quantity in the backend cart.
   * @param {Object} item
   * @param {number} item.productId
   * @param {number} item.quantity
   * @param {string|null} [item.size=null]
   * @returns {Promise<Object>}
   */
  async updateItem({ productId, quantity, size = null }) {
    const res = await apiClient.put("/cart/update", {
      product_id: Number(productId),
      quantity: Number(quantity),
      size: size || null,
    });
    return res.data;
  },

  /**
   * Removes an item from the backend cart.
   * @param {Object} item
   * @param {number} item.productId
   * @param {string|null} [item.size=null]
   * @returns {Promise<Object>}
   */
  async removeItem({ productId, size = null }) {
    const res = await apiClient.delete("/cart/remove", {
      data: {
        product_id: Number(productId),
        size: size || null,
      },
    });
    return res.data;
  },

  /**
   * Applies an AI/negotiated discount percentage to the cart.
   * @param {number} discountPercentage
   * @returns {Promise<Object>}
   */
  async applyDiscount(discountPercentage) {
    const res = await apiClient.patch("/cart/discount", {
      discount_percentage: Number(discountPercentage),
    });
    return res.data;
  },

  /**
   * Clears all items in the user's cart on backend.
   * @returns {Promise<Object>}
   */
  async clearCart() {
    const res = await apiClient.delete("/cart/clear");
    return res.data;
  },
};

export default cartService;
