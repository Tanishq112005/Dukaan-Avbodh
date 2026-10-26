import React, { useState } from "react";
import { Ruler, Check, Sparkles, ShoppingBag } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function SizeAdvisorCard({ data, onProductClick }) {
  const addToCart = useStore((state) => state.addToCart);
  const [added, setAdded] = useState(false);

  const product = data?.product || {};
  const recommendedSize = data?.recommended_size || data?.size || "L";
  const fitType = data?.fit_type || "True to Size · Regular Fit";
  const userHeight = data?.height || "5'10\" - 6'0\"";
  const rationale = data?.rationale || "Based on tailored shoulder seam draping and breathable luxury cotton weave.";

  const finalId = product.id || product.product_id;
  const imgUrl =
    product.image_url ||
    product.image ||
    (finalId ? `https://picsum.photos/seed/${finalId}/400/400` : "https://picsum.photos/seed/dukaan-size/400/400");

  const sellingPrice =
    product.discount > 0 && product.price
      ? Math.round(Number(product.price) / (1 - product.discount / 100))
      : (product.price !== undefined && product.price !== null ? Number(product.price) : 0);

  const price = sellingPrice ? `₹${sellingPrice.toLocaleString("en-IN")}` : null;

  const handleQuickAddRecommended = (e) => {
    e.preventDefault();
    if (finalId) {
      addToCart(
        {
          id: finalId,
          name: product.name || "Apparel Item",
          price: sellingPrice,
          image_url: imgUrl,
          brand: product.brand || "DUKAAN",
        },
        1,
        recommendedSize,
        "Default"
      );
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    }
  };

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-stone-50 via-white to-stone-50 border border-stone-200/90 rounded-2xl p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-stone-200/60">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-900">
          <Ruler size={14} className="text-[#C45C26]" />
          <span>Stylist Fit Advisor</span>
        </div>
        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#C45C26]/10 text-[#C45C26] border border-[#C45C26]/20">
          Personalized Size
        </span>
      </div>

      {/* Recommended Size Highlight */}
      <div className="flex items-center gap-3.5 bg-stone-100/80 rounded-xl p-3 border border-stone-200/60 mb-3">
        {finalId && (
          <div className="w-14 h-14 rounded-lg bg-stone-200 overflow-hidden flex-shrink-0 border border-stone-300/50">
            <img src={imgUrl} alt={product.name} className="w-full h-full object-cover" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-medium text-stone-500 truncate">
            {product.name || "Recommended Garment"}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-lg font-black text-stone-900">
              Size {recommendedSize}
            </span>
            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200/50">
              {fitType}
            </span>
          </div>
        </div>
        {price && <span className="font-bold text-xs text-stone-900">{price}</span>}
      </div>

      {/* Fit Rationale */}
      <p className="text-xs text-stone-600 leading-relaxed mb-3">
        <span className="font-semibold text-stone-800">Stylist Note: </span>
        {rationale}
      </p>

      {/* Action Button */}
      {finalId && (
        <button
          type="button"
          onClick={handleQuickAddRecommended}
          className={`w-full py-2.5 px-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs ${
            added
              ? "bg-emerald-600 text-white"
              : "bg-stone-900 hover:bg-[#6e1423] text-white"
          }`}
        >
          {added ? (
            <>
              <Check size={14} strokeWidth={2.5} />
              <span>Added Size {recommendedSize} to Bag</span>
            </>
          ) : (
            <>
              <ShoppingBag size={14} />
              <span>Add Size {recommendedSize} to Bag</span>
            </>
          )}
        </button>
      )}
    </div>
  );
}
