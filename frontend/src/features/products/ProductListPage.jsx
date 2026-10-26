import { useEffect, useState, useMemo } from "react";
import { useStore } from "../../store/useStore";
import { FilterSidebar } from "./FilterSidebar";
import { ProductCard } from "../../components/ui/ProductCard";
import { ChevronRight, SlidersHorizontal, X, ArrowUpDown, Sparkles, MessageCircle } from "lucide-react";
import { Loader } from "../../components/ui/Loader";
import { Link } from "react-router-dom";

export function ProductListPage() {
  const {
    products,
    setProducts,
    fetchProducts,
    searchQuery,
    setSearchQuery,
    selectedType,
    setSelectedType,
    maxPrice,
    setMaxPrice,
    setIsAgentOpen,
  } = useStore();

  const [loading, setLoading] = useState(products.length === 0);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [sortBy, setSortBy] = useState("featured");

  useEffect(() => {
    let mounted = true;
    if (products.length === 0) {
      fetchProducts()
        .then((items) => {
          if (mounted && (!items || items.length === 0)) {
            setProducts([
              { id: 1, name: "Gradient Graphic T-shirt", price: 145, rating: 4.5, discount: 0, type: "t-shirt", brand: "ZARA", description: "Awesome gradient t-shirt for summer.", sizes: "S,M,L" },
              { id: 2, name: "Polo with Tipping Details", price: 180, rating: 4.5, discount: 0, type: "shirt", brand: "GUCCI", description: "Classic polo shirt with tipping details.", sizes: "M,L,XL" },
              { id: 3, name: "Black Striped T-shirt", price: 120, rating: 5, discount: 30, type: "t-shirt", brand: "VERSACE", description: "Elegant black striped t-shirt.", sizes: "S,M,L,XL" },
              { id: 4, name: "Skinny Fit Jeans", price: 240, rating: 3.5, discount: 20, type: "jeans", brand: "CALVIN KLEIN", description: "Comfortable skinny fit jeans.", sizes: "M,L" },
              { id: 5, name: "Vertical Striped Shirt", price: 212, rating: 5.0, discount: 15, type: "shirt", brand: "RALPH LAUREN", description: "Refined button-down shirt.", sizes: "M,L,XL" },
              { id: 6, name: "Courage Graphic Tee", price: 145, rating: 4.0, discount: 0, type: "t-shirt", brand: "VERSACE", description: "Statement designer tee.", sizes: "S,M,L" },
              { id: 7, name: "Loose Fit Bermuda Shorts", price: 80, rating: 3.5, discount: 0, type: "short", brand: "CALVIN KLEIN", description: "Relaxed comfort shorts.", sizes: "S,M,L" },
              { id: 8, name: "Faded Vintage Denim Jeans", price: 210, rating: 4.8, discount: 10, type: "jeans", brand: "PRADA", description: "Tailored wash denim.", sizes: "30,32,34" },
            ]);
          }
        })
        .finally(() => {
          if (mounted) setLoading(false);
        });
    } else {
      setLoading(false);
    }
    return () => {
      mounted = false;
    };
  }, [fetchProducts, products.length, setProducts]);

  // Filter and Sort Pipeline
  const filteredProducts = useMemo(() => {
    let list = products.filter((p) => {
      const matchesSearch = (p.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.brand || "").toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = selectedType === "" || (p.type || "").toLowerCase() === selectedType.toLowerCase();
      const matchesPrice = (p.price || 0) <= maxPrice;
      return matchesSearch && matchesType && matchesPrice;
    });

    switch (sortBy) {
      case "price-asc":
        return list.slice().sort((a, b) => (a.price || 0) - (b.price || 0));
      case "price-desc":
        return list.slice().sort((a, b) => (b.price || 0) - (a.price || 0));
      case "rating":
        return list.slice().sort((a, b) => (b.rating || 0) - (a.rating || 0));
      case "discount":
        return list.slice().sort((a, b) => (b.discount || 0) - (a.discount || 0));
      default:
        return list;
    }
  }, [products, searchQuery, selectedType, maxPrice, sortBy]);

  const activeFiltersCount = (selectedType ? 1 : 0) + (maxPrice < 6000 ? 1 : 0) + (searchQuery ? 1 : 0);

  const clearAllFilters = () => {
    setSelectedType("");
    setMaxPrice(6000);
    setSearchQuery("");
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      {/* Breadcrumb Navigation */}
      <nav className="flex items-center gap-2 text-xs sm:text-sm text-stone-500 mb-4 sm:mb-6">
        <Link to="/" className="hover:text-stone-900 transition-colors">Home</Link>
        <ChevronRight size={14} className="text-stone-400" />
        <Link to="/products" className="hover:text-stone-900 transition-colors">Catalog</Link>
        {selectedType && (
          <>
            <ChevronRight size={14} className="text-stone-400" />
            <span className="text-stone-900 font-semibold capitalize">{selectedType}</span>
          </>
        )}
      </nav>

      {/* Main Page Layout: items-start allows sticky children to float along scroll track */}
      <div className="flex flex-col md:flex-row items-start gap-8 lg:gap-10">
        {/* Desktop Sticky Sidebar */}
        <FilterSidebar />

        {/* Mobile Filters Drawer Modal */}
        {showMobileFilters && (
          <div className="fixed inset-0 z-50 flex md:hidden">
            <div
              className="fixed inset-0 bg-stone-950/50 backdrop-blur-xs transition-opacity"
              onClick={() => setShowMobileFilters(false)}
            />
            <div className="relative ml-auto w-full max-w-xs h-full bg-white shadow-2xl p-6 overflow-y-auto">
              <FilterSidebar isMobile onClose={() => setShowMobileFilters(false)} />
            </div>
          </div>
        )}

        {/* Product Catalog Content Area */}
        <div className="flex-1 min-w-0 w-full">
          {/* Sticky Header & Controls Bar - Pinned right below the navbar */}
          <div className="sticky top-[96px] sm:top-[102px] z-20 bg-[#FBF8F3]/95 backdrop-blur-md pt-2 pb-4 mb-6 border-b border-stone-200/80 transition-all">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <p className="text-[11px] tracking-widest uppercase text-[#C45C26] font-bold mb-1">
                  Designer Collections
                </p>
                <h1 className="font-display text-2xl sm:text-3xl font-extrabold uppercase text-stone-900 tracking-tight">
                  {selectedType ? `${selectedType}s` : "All Apparel"}
                </h1>
              </div>

              <div className="flex items-center gap-3">
                {/* Mobile Filter Toggle Button */}
                <button
                  onClick={() => setShowMobileFilters(true)}
                  className="md:hidden flex items-center gap-2 px-3.5 py-2 rounded-xl border border-stone-300 text-stone-700 text-xs font-semibold hover:bg-stone-50 transition-colors cursor-pointer"
                >
                  <SlidersHorizontal size={14} />
                  <span>Filters</span>
                  {activeFiltersCount > 0 && (
                    <span className="w-5 h-5 rounded-full bg-stone-900 text-white text-[10px] flex items-center justify-center">
                      {activeFiltersCount}
                    </span>
                  )}
                </button>

                {/* Sort Dropdown */}
                <div className="flex items-center gap-2 bg-white border border-stone-200/90 rounded-xl px-3 py-1.5 shadow-xs">
                  <ArrowUpDown size={13} className="text-stone-400" />
                  <span className="text-xs text-stone-400 hidden sm:inline">Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="text-xs font-semibold text-stone-800 bg-transparent outline-none cursor-pointer pr-1"
                  >
                    <option value="featured">Featured Edit</option>
                    <option value="price-asc">Price: Low to High</option>
                    <option value="price-desc">Price: High to Low</option>
                    <option value="rating">Top Rated</option>
                    <option value="discount">Biggest Discount</option>
                  </select>
                </div>

                <span className="text-stone-400 text-xs hidden sm:inline font-medium">
                  {filteredProducts.length} pieces
                </span>
              </div>
            </div>

            {/* Active Filter Chips embedded inside the sticky bar */}
            {activeFiltersCount > 0 && (
              <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-stone-200/60">
                <span className="text-xs text-stone-400 font-medium mr-1">Active filters:</span>

                {selectedType && (
                  <button
                    onClick={() => setSelectedType("")}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-800 hover:bg-stone-200 transition-colors"
                  >
                    <span>Category: {selectedType}</span>
                    <X size={12} />
                  </button>
                )}

                {maxPrice < 6000 && (
                  <button
                    onClick={() => setMaxPrice(6000)}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-800 hover:bg-stone-200 transition-colors"
                  >
                    <span>Under ₹{maxPrice.toLocaleString("en-IN")}</span>
                    <X size={12} />
                  </button>
                )}

                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-800 hover:bg-stone-200 transition-colors"
                  >
                    <span>"{searchQuery}"</span>
                    <X size={12} />
                  </button>
                )}

                <button
                  onClick={clearAllFilters}
                  className="text-xs text-[#6e1423] font-semibold hover:underline ml-2 cursor-pointer"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>

          {/* Product Cards Grid */}
          {filteredProducts.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
              {filteredProducts.map((p, i) => (
                <ProductCard key={p.id || i} {...p} index={i} />
              ))}
            </div>
          ) : (
            /* Empty State */
            <div className="text-center py-16 px-4 bg-white rounded-3xl border border-stone-200/80 shadow-xs max-w-lg mx-auto">
              <div className="w-14 h-14 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-4 text-[#C45C26]">
                <Sparkles size={24} />
              </div>
              <h3 className="font-display text-xl font-bold text-stone-900 mb-2">
                No matching garments found
              </h3>
              <p className="text-stone-500 text-sm max-w-sm mx-auto mb-6">
                Try loosening your filters, adjusting your price ceiling, or chat directly with our AI Stylist to source what you need.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                <button
                  onClick={clearAllFilters}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-full bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-semibold tracking-wider uppercase transition-colors cursor-pointer"
                >
                  Clear all filters
                </button>
                <button
                  onClick={() => setIsAgentOpen(true)}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-full border border-stone-300 hover:bg-stone-50 text-stone-800 text-xs font-semibold tracking-wider uppercase transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <MessageCircle size={14} className="text-[#C45C26]" />
                  <span>Ask Stylist</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
