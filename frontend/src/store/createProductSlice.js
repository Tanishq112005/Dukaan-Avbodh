export const createProductSlice = (set) => ({
  products: [],
  setProducts: (products) => set({ products }),
  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),
  selectedType: "",
  setSelectedType: (type) => set({ selectedType: type }),
  maxPrice: 3000,
  setMaxPrice: (price) => set({ maxPrice: price }),
});
