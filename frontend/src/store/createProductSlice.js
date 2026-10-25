import { productService } from "../services/productService";

export const createProductSlice = (set, get) => ({
  products: [],
  isLoadingProducts: false,
  productError: null,
  setProducts: (products) => set({ products }),
  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),
  selectedType: "",
  setSelectedType: (type) => set({ selectedType: type }),
  maxPrice: 3000,
  setMaxPrice: (price) => set({ maxPrice: price }),

  fetchProducts: async (force = false) => {
    if (!force && get().products.length > 0) {
      return get().products;
    }
    set({ isLoadingProducts: true, productError: null });
    try {
      const items = await productService.getAllProducts();
      if (Array.isArray(items) && items.length > 0) {
        set({ products: items, isLoadingProducts: false });
        return items;
      }
      set({ isLoadingProducts: false });
      return get().products;
    } catch (err) {
      console.warn("[ProductSlice] Error fetching products, using cached or fallback:", err);
      set({
        productError: err.message || "Failed to load products",
        isLoadingProducts: false,
      });
      return get().products;
    }
  },
});
