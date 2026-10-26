import { Link } from "react-router-dom";
import { Star } from "lucide-react";

export function ProductCard({
  id,
  product_id,
  name,
  price,
  rating,
  discount,
  image_url,
  image,
  brand,
  type,
  index,
  eager = false,
  size = "normal",
  onProductClick,
}) {
  const finalId = id || product_id;
  const imgUrl = image_url || image || (finalId ? `https://picsum.photos/seed/${finalId}/600/750` : "https://picsum.photos/seed/dukaan/600/750");

  // Selling price (base list price before discount, e.g. 858)
  const displayPrice = discount > 0 && price
    ? `₹${Math.round(Number(price) / (1 - discount / 100)).toLocaleString("en-IN")}`
    : (price !== undefined && price !== null ? `₹${Number(price).toLocaleString("en-IN")}` : "₹0");

  // Compact variant for Chatbot suggestions and mini carousels
  if (size === "small") {
    return (
      <div className="flex-shrink-0 w-28 sm:w-32 bg-white border border-stone-200/90 rounded-xl overflow-hidden hover:border-stone-400 hover:shadow-md transition-all duration-200 flex flex-col group">
        <Link
          to={finalId ? `/product/${finalId}` : "#"}
          onClick={() => onProductClick?.(finalId)}
          className="relative aspect-square bg-stone-100 overflow-hidden block"
        >
          <img
            src={imgUrl}
            alt={name || "Product"}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ease-out"
            loading="lazy"
            decoding="async"
            width="160"
            height="160"
          />
          {/* Rating pill on image */}
          <div className="absolute bottom-1 left-1 bg-white/95 backdrop-blur-xs text-stone-800 text-[9px] font-bold px-1 py-0.2 rounded shadow-xs flex items-center gap-0.5 border border-stone-200/50">
            <span>{rating ? Number(rating).toFixed(1) : "4.3"}</span>
            <Star size={8} className="text-emerald-700 fill-emerald-600" />
          </div>
        </Link>
        <div className="p-1.5 flex flex-col flex-1 justify-between bg-white">
          <div>
            {brand && (
              <p className="text-[8px] font-bold tracking-wider uppercase text-stone-400 truncate">
                {brand}
              </p>
            )}
            <Link
              to={finalId ? `/product/${finalId}` : "#"}
              onClick={() => onProductClick?.(finalId)}
              className="text-[11px] font-semibold text-stone-900 line-clamp-1 hover:text-[#6e1423] transition-colors leading-tight block"
              title={name}
            >
              {name || "View Item"}
            </Link>
          </div>
          <div className="pt-1 mt-1 border-t border-stone-100">
            <span className="text-[11px] font-bold text-stone-900">{displayPrice}</span>
          </div>
        </div>
      </div>
    );
  }

  // Standard Product Card
  return (
    <div className="group flex flex-col h-full bg-white border border-stone-200/80 rounded-xl overflow-hidden hover:border-stone-300 hover:shadow-md transition-all duration-200">
      <Link
        to={finalId ? `/product/${finalId}` : "#"}
        onClick={() => onProductClick?.(finalId)}
        className="relative aspect-square bg-stone-100 overflow-hidden block"
      >
        <img
          src={imgUrl}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-104 transition-transform duration-400 ease-out"
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          width="400"
          height="400"
          onLoad={(e) => e.currentTarget.setAttribute("data-loaded", "true")}
        />

        {/* Rating Badge overlay at bottom-left of image */}
        <div className="absolute bottom-1.5 left-1.5 z-10 bg-white/95 backdrop-blur-xs text-stone-800 text-[10px] font-bold px-1.5 py-0.5 rounded shadow-xs flex items-center gap-1 border border-stone-200/60">
          <span>{rating ? Number(rating).toFixed(1) : "4.3"}</span>
          <Star size={9} className="text-emerald-700 fill-emerald-600" />
        </div>
      </Link>

      <div className="p-2 sm:p-2.5 flex flex-col flex-1 justify-between bg-white">
        <div>
          {/* Brand & Type */}
          <div className="flex items-center justify-between gap-1 mb-0.5">
            <span className="text-[10px] font-bold tracking-wider uppercase text-stone-400 truncate">
              {brand || "DUKAAN"}
            </span>
            {type && (
              <span className="text-[9px] uppercase font-medium text-stone-400 bg-stone-100 px-1 py-0.2 rounded-xs">
                {type}
              </span>
            )}
          </div>

          {/* Product Name */}
          <Link
            to={finalId ? `/product/${finalId}` : "#"}
            onClick={() => onProductClick?.(finalId)}
            className="block text-xs sm:text-[13px] font-semibold text-stone-900 hover:text-[#6e1423] transition-colors leading-snug line-clamp-1"
            title={name}
          >
            {name}
          </Link>
        </div>

        {/* Pricing Row: Only single clean selling price (no second price, no strikethrough, no add-to-cart button) */}
        <div className="pt-1.5 mt-1.5 border-t border-stone-100">
          <span className="text-xs sm:text-sm font-bold text-stone-900">
            {displayPrice}
          </span>
        </div>
      </div>
    </div>
  );
}
