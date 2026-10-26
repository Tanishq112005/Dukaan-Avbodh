import { useState } from "react";
import { ProductCard } from "../../components/ui/ProductCard";
import { Link } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";

export function ProductSection({ title = "NEW ARRIVALS", products = [], eager = false }) {
  const [activeTab, setActiveTab] = useState("all");

  const categories = [
    { key: "all", label: "All Items" },
    { key: "t-shirt", label: "T-Shirts" },
    { key: "shirt", label: "Shirts" },
    { key: "jeans", label: "Jeans" },
    { key: "hoodie", label: "Hoodies" },
  ];

  const filteredProducts = activeTab === "all"
    ? products
    : products.filter((p) => (p.type || "").toLowerCase().includes(activeTab.toLowerCase()));

  const displayList = filteredProducts.slice(0, 8);

  return (
    <section className="py-14 md:py-18 border-t border-stone-200/80 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-7">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-bold tracking-widest text-[#C45C26] uppercase mb-1">
              <Sparkles size={13} />
              <span>Curated Selection</span>
            </div>
            <h2 className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight uppercase text-stone-900">
              {title}
            </h2>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-hide">
            {categories.map((c) => (
              <button
                key={c.key}
                onClick={() => setActiveTab(c.key)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                  activeTab === c.key
                    ? "bg-stone-900 text-white shadow-xs"
                    : "bg-stone-100 hover:bg-stone-200/80 text-stone-600"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* Product Grid: 4 cards per row */}
        {displayList.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-5">
            {displayList.map((p, i) => (
              <ProductCard
                key={p.id || i}
                {...p}
                index={i}
                eager={eager && i < 2}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-stone-50 rounded-2xl border border-stone-200/60 p-6">
            <p className="text-stone-500 text-sm">No items found in this category.</p>
            <button
              onClick={() => setActiveTab("all")}
              className="mt-3 text-xs font-semibold text-[#6e1423] underline underline-offset-4 cursor-pointer"
            >
              Reset to all items
            </button>
          </div>
        )}

        {/* View All Button */}
        <div className="mt-10 text-center">
          <Link
            to="/products"
            className="inline-flex items-center gap-2 px-7 py-3 rounded-full border border-stone-900 text-stone-900 hover:bg-stone-900 hover:text-white text-xs font-bold tracking-widest uppercase transition-all duration-300 shadow-xs hover:shadow-md cursor-pointer"
          >
            <span>View Complete Collection</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </section>
  );
}
