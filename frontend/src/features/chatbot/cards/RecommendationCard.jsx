import React from "react";
import { Link } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";

export function RecommendationCard({ data, onProductClick }) {
  const products = data?.products || [];

  if (!products || products.length === 0) return null;

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
          const imgUrl =
            p.image_url ||
            p.image ||
            (finalId
              ? `https://picsum.photos/seed/${finalId}/400/500`
              : "https://picsum.photos/seed/dukaan/400/500");
          const formattedPrice = `₹${Number(p.price || 0).toLocaleString("en-IN")}`;

          return (
            <Link
              key={finalId ? `rec-card-${finalId}` : `item-${idx}`}
              to={`/product/${finalId}`}
              onClick={() => onProductClick?.(p)}
              className="group flex-shrink-0 w-36 sm:w-40 bg-white border border-stone-200/80 rounded-xl overflow-hidden hover:border-[#C45C26]/60 hover:shadow-md transition-all duration-200 snap-start flex flex-col justify-between cursor-pointer"
              title={`View ${p.name}`}
            >
              {/* Image thumbnail linking to product detail page */}
              <div className="relative aspect-[4/5] bg-stone-100 overflow-hidden block">
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

              {/* Product Info: Only Product Name and Selling Price */}
              <div className="p-2.5 flex-1 flex flex-col justify-between">
                <div>
                  <h4 className="font-semibold text-xs text-stone-900 line-clamp-1 group-hover:text-[#C45C26] transition-colors leading-tight">
                    {p.name || "Curated Apparel"}
                  </h4>
                  <div className="flex items-center justify-between mt-1.5">
                    <span className="font-bold text-xs sm:text-sm text-stone-900">
                      {formattedPrice}
                    </span>
                    <span className="text-[10px] font-semibold text-stone-400 group-hover:text-[#C45C26] transition-colors flex items-center gap-0.5">
                      <span>View</span>
                      <ArrowRight size={10} />
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
