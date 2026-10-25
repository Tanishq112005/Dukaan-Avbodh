import apiClient from "./api.js";

/**
 * Service for Product catalog and management.
 * Interfaces with Product/routes: /products/*
 */
export const productService = {
  /**
   * Fetches all products.
   * @returns {Promise<Array>} List of products
   */
  async getAllProducts() {
    try {
      const res = await apiClient.get("/products/item");
      return res.data.products || res.data || [];
    } catch (err) {
      // Fallback attempt to in-stock endpoint if /item fails or requires different permissions
      try {
        const fallbackRes = await apiClient.get("/products/item/Stock");
        return fallbackRes.data.products || fallbackRes.data || [];
      } catch (fallbackErr) {
        throw err;
      }
    }
  },

  /**
   * Fetches only products currently in stock.
   * @returns {Promise<Array>}
   */
  async getInStockProducts() {
    const res = await apiClient.get("/products/item/Stock");
    return res.data.products || res.data || [];
  },

  /**
   * Fetches products filtered by category/type (e.g. t-shirt, shirt, jeans).
   * @param {string} productType
   * @returns {Promise<Array>}
   */
  async getProductsByType(productType) {
    const res = await apiClient.get(`/products/type/${encodeURIComponent(productType)}`);
    return res.data.products || res.data || [];
  },

  /**
   * Fetches a single product by ID.
   * Uses catalog lookup with cache / fallback.
   * @param {number|string} productId
   * @returns {Promise<Object>}
   */
  async getProductById(productId) {
    const products = await this.getAllProducts();
    const found = products.find((p) => String(p.id) === String(productId));
    if (found) return found;
    throw new Error(`Product #${productId} not found.`);
  },

  /**
   * Merchant: Adds a new product to the catalog.
   * @param {Object} product
   * @returns {Promise<Object>}
   */
  async addProduct(product) {
    const res = await apiClient.post("/products/add", product);
    return res.data;
  },

  /**
   * Merchant: Updates an existing product.
   * @param {number|string} productId
   * @param {Object} updates
   * @returns {Promise<Object>}
   */
  async updateProduct(productId, updates) {
    const res = await apiClient.patch(`/products/update/${productId}`, updates);
    return res.data;
  },

  /**
   * Merchant: Deletes a product.
   * @param {number|string} productId
   * @returns {Promise<Object>}
   */
  async deleteProduct(productId) {
    const res = await apiClient.delete(`/products/delete/${productId}`);
    return res.data;
  },
};

export default productService;
