import { useState } from "react";
import { Link } from "react-router-dom";
import { Star, ShoppingBag, Check } from "lucide-react";
import { useStore } from "../../store/useStore";

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
  const addToCart = useStore((state) => state.addToCart);
  const [justAdded, setJustAdded] = useState(false);

  const handleQuickAdd = (e) => {
    e.preventDefault();
    e.stopPropagation();

    const productPayload = {
      id: finalId,
      name: name || "Product",
      price: price !== undefined && price !== null ? price : 0,
      image_url: imgUrl,
      brand: brand || "DUKAAN",
      type: type || "apparel",
    };

    addToCart(productPayload, 1, "M", "Default");
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1600);
  };

  const formattedPrice = price !== undefined && price !== null
    ? `₹${Number(price).toLocaleString("en-IN")}`
    : "₹0";

  const originalPrice = discount > 0 && price
    ? `₹${Math.round(Number(price) / (1 - discount / 100)).toLocaleString("en-IN")}`
    : null;

  // Compact variant for Chatbot suggestions and mini carousels
  if (size === "small") {
    return (
      <div className="flex-shrink-0 w-32 sm:w-40 bg-white border border-stone-200/90 rounded-2xl overflow-hidden hover:border-stone-400 hover:shadow-md transition-all duration-300 flex flex-col group">
        <Link
          to={finalId ? `/product/${finalId}` : "#"}
          onClick={() => onProductClick?.(finalId)}
          className="relative aspect-[4/5] bg-stone-100 overflow-hidden block"
        >
          <img
            src={imgUrl}
            alt={name || "Product"}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
            loading="lazy"
            decoding="async"
            width="160"
            height="200"
          />
          {discount > 0 && (
            <span className="absolute top-2 left-2 bg-[#6e1423] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full shadow-xs">
              -{discount}%
            </span>
          )}
        </Link>
        <div className="p-2 sm:p-2.5 flex flex-col flex-1 justify-between bg-white">
          <div>
            {brand && (
              <p className="text-[9px] font-bold tracking-widest uppercase text-stone-400 truncate mb-0.5">
                {brand}
              </p>
            )}
            <Link
              to={finalId ? `/product/${finalId}` : "#"}
              onClick={() => onProductClick?.(finalId)}
              className="text-xs font-semibold text-stone-900 line-clamp-1 hover:text-[#6e1423] transition-colors"
              title={name}
            >
              {name || "View Item"}
            </Link>
          </div>
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-stone-100">
            <div>
              <span className="text-xs font-bold text-stone-900">{formattedPrice}</span>
              {originalPrice && (
                <span className="text-[10px] text-stone-400 line-through ml-1">{originalPrice}</span>
              )}
            </div>
            <button
              onClick={handleQuickAdd}
              type="button"
              title="Add to Cart"
              className={`p-1.5 rounded-full transition-all cursor-pointer ${
                justAdded
                  ? "bg-emerald-600 text-white"
                  : "bg-stone-900 hover:bg-[#6e1423] text-white"
              }`}
            >
              {justAdded ? <Check size={11} strokeWidth={2.5} /> : <ShoppingBag size={11} />}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Standard Catalog & Grid Product Card
  return (
    <div className="group flex flex-col h-full bg-white border border-stone-200/80 rounded-2xl overflow-hidden hover:border-stone-400/90 shadow-[0_2px_12px_-2px_rgba(0,0,0,0.04)] hover:shadow-[0_16px_36px_-6px_rgba(20,16,12,0.12)] transition-all duration-300">
      <Link
        to={finalId ? `/product/${finalId}` : "#"}
        onClick={() => onProductClick?.(finalId)}
        className="relative aspect-[3/4] bg-stone-100 overflow-hidden block"
      >
        {/* Discount badge */}
        {discount > 0 && (
          <span className="absolute top-2.5 left-2.5 sm:top-3 sm:left-3 z-10 bg-[#6e1423] text-white text-[9px] sm:text-xs font-bold px-2 py-0.5 rounded-full shadow-sm tracking-wide">
            -{discount}% OFF
          </span>
        )}

        {/* Index counter if specified */}
        {typeof index === "number" && !discount && (
          <span className="absolute top-2.5 left-2.5 sm:top-3 sm:left-3 z-10 text-[9px] sm:text-[10px] font-semibold text-stone-600 bg-white/90 backdrop-blur-xs px-2 py-0.5 rounded-full border border-stone-200/60">
            #{String(index + 1).padStart(2, "0")}
          </span>
        )}

        <img
          src={imgUrl}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          width="600"
          height="800"
          onLoad={(e) => e.currentTarget.setAttribute("data-loaded", "true")}
        />

        {/* Quick Add overlay button on hover for desktop */}
        <div className="hidden sm:block absolute inset-x-3 bottom-3 z-10 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-1 group-hover:translate-y-0">
          <button
            onClick={handleQuickAdd}
            type="button"
            className={`w-full py-2.5 px-3 rounded-xl text-xs font-semibold tracking-wide flex items-center justify-center gap-1.5 shadow-md backdrop-blur-md transition-all cursor-pointer ${
              justAdded
                ? "bg-emerald-600 text-white"
                : "bg-white/95 hover:bg-stone-900 text-stone-900 hover:text-white border border-stone-200"
            }`}
          >
            {justAdded ? (
              <>
                <Check size={14} className="text-white" strokeWidth={2.5} />
                <span>Added to Bag</span>
              </>
            ) : (
              <>
                <ShoppingBag size={14} />
                <span>Quick Add</span>
              </>
            )}
          </button>
        </div>
      </Link>

      <div className="p-3 sm:p-4.5 flex flex-col flex-1 justify-between bg-white">
        <div>
          {/* Brand & Type */}
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[10px] sm:text-[11px] font-bold tracking-widest uppercase text-stone-400 truncate">
              {brand || "ATELIER"}
            </span>
            {type && (
              <span className="text-[9px] sm:text-[10px] uppercase font-medium text-stone-400 bg-stone-100 px-1.5 py-0.5 rounded-sm">
                {type}
              </span>
            )}
          </div>

          {/* Product Name */}
          <Link
            to={finalId ? `/product/${finalId}` : "#"}
            onClick={() => onProductClick?.(finalId)}
            className="block text-xs sm:text-base font-semibold text-stone-900 hover:text-[#6e1423] transition-colors leading-snug line-clamp-1 mb-1.5 sm:mb-2"
            title={name}
          >
            {name}
          </Link>

          {/* Rating */}
          <div className="flex items-center gap-1.5 mb-2.5 sm:mb-3">
            <div className="flex items-center text-amber-500">
              <Star size={12} fill="currentColor" strokeWidth={0} />
            </div>
            <span className="text-[11px] sm:text-xs font-semibold text-stone-700">
              {rating ? Number(rating).toFixed(1) : "4.5"}
            </span>
            <span className="text-[10px] sm:text-[11px] text-stone-400">
              ({rating ? Math.round(Number(rating) * 24 + 18) : 84})
            </span>
          </div>
        </div>

        {/* Pricing Row with Direct Mobile Quick-Add Button */}
        <div className="flex items-center justify-between pt-2 border-t border-stone-100">
          <div>
            <div className="flex items-baseline gap-1.5 sm:gap-2">
              <span className="text-sm sm:text-lg font-bold text-stone-900">
                {formattedPrice}
              </span>
              {originalPrice && (
                <span className="text-[10px] sm:text-xs text-stone-400 line-through">
                  {originalPrice}
                </span>
              )}
            </div>
            {discount > 0 && (
              <span className="inline-block sm:hidden text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded mt-0.5">
                Save {discount}%
              </span>
            )}
          </div>

          {/* Mobile Tap-To-Add button */}
          <button
            onClick={handleQuickAdd}
            type="button"
            className={`sm:hidden p-2 rounded-xl transition-all cursor-pointer ${
              justAdded
                ? "bg-emerald-600 text-white"
                : "bg-stone-900 text-white hover:bg-[#6e1423]"
            }`}
            title="Add to Bag"
          >
            {justAdded ? <Check size={13} strokeWidth={2.5} /> : <ShoppingBag size={13} />}
          </button>

          {discount > 0 && (
            <span className="hidden sm:inline-block text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-md">
              Save {discount}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
