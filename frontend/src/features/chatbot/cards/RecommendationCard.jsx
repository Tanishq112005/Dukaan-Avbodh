import React, { useState } from "react";
import { Sparkles, ShoppingBag, Check, ArrowRight } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function RecommendationCard({ data, onProductClick }) {
  const products = data?.products || [];
  const addToCart = useStore((state) => state.addToCart);
  const [addedIds, setAddedIds] = useState({});

  if (!products || products.length === 0) return null;

  const handleQuickAdd = (e, product) => {
    e.stopPropagation();
    const finalId = product.id || product.product_id;
    addToCart(
      {
        id: finalId,
        name: product.name || "Product",
        price: product.price || 0,
        image_url: product.image_url || product.image,
        brand: product.brand || "DUKAAN",
        type: product.type || "apparel",
      },
      1,
      "M",
      product.color || "Default"
    );

    setAddedIds((prev) => ({ ...prev, [finalId]: true }));
    setTimeout(() => {
      setAddedIds((prev) => ({ ...prev, [finalId]: false }));
    }, 1800);
  };

  return (
    <div className="w-full mt-3 bg-stone-50/80 border border-stone-200/90 rounded-2xl p-3.5 shadow-xs">
      <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-stone-200/60">
        <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase text-stone-800">
          <Sparkles size={13} className="text-[#C45C26]" />
          <span>{data.title || "Curated Stylist Picks"}</span>
        </div>
        <span className="text-[11px] font-medium text-stone-500">
          {products.length} {products.length === 1 ? "piece" : "pieces"}
        </span>
      </div>

      <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-hide snap-x">
        {products.map((p, idx) => {
          const finalId = p.id || p.product_id;
          const isAdded = !!addedIds[finalId];
          const imgUrl =
            p.image_url ||
            p.image ||
            (finalId
              ? `https://picsum.photos/seed/${finalId}/400/500`
              : "https://picsum.photos/seed/dukaan/400/500");
          const formattedPrice = `₹${Number(p.price || 0).toLocaleString("en-IN")}`;

          return (
            <div
              key={finalId ? `rec-card-${finalId}` : `item-${idx}`}
              onClick={() => onProductClick?.(p)}
              className="group flex-shrink-0 w-36 sm:w-40 bg-white border border-stone-200/80 rounded-xl overflow-hidden hover:border-[#C45C26]/50 hover:shadow-md transition-all duration-200 cursor-pointer snap-start flex flex-col justify-between"
            >
              {/* Image thumbnail */}
              <div className="relative aspect-[4/5] bg-stone-100 overflow-hidden">
                <img
                  src={imgUrl}
                  alt={p.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                {p.brand && (
                  <span className="absolute top-1.5 left-1.5 bg-stone-900/80 backdrop-blur-xs text-[9px] font-bold text-white uppercase px-1.5 py-0.5 rounded-sm tracking-wider">
                    {p.brand}
                  </span>
                )}
              </div>

              {/* Product Info */}
              <div className="p-2.5 flex-1 flex flex-col justify-between">
                <div>
                  <h4 className="font-semibold text-xs text-stone-900 line-clamp-1 group-hover:text-[#C45C26] transition-colors">
                    {p.name || "Curated Apparel"}
                  </h4>
                  <div className="flex items-baseline gap-1.5 mt-1">
                    <span className="font-bold text-xs text-stone-900">{formattedPrice}</span>
                    {p.discount > 0 && (
                      <span className="text-[10px] text-emerald-700 font-semibold">
                        {p.discount}% OFF
                      </span>
                    )}
                  </div>
                </div>

                {/* Quick Add CTA */}
                <button
                  type="button"
                  onClick={(e) => handleQuickAdd(e, p)}
                  className={`mt-2 w-full py-1.5 px-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition-all ${
                    isAdded
                      ? "bg-emerald-600 text-white"
                      : "bg-stone-900 hover:bg-[#6e1423] text-white"
                  }`}
                >
                  {isAdded ? (
                    <>
                      <Check size={12} />
                      <span>Added!</span>
                    </>
                  ) : (
                    <>
                      <ShoppingBag size={12} />
                      <span>Add to Bag</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
