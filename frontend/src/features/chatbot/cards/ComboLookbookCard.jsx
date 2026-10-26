import React, { useState } from "react";
import { Sparkles, Plus, Check, ShoppingBag, ArrowRight } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function ComboLookbookCard({ data, onProductClick }) {
  const addToCart = useStore((state) => state.addToCart);
  const [added, setAdded] = useState(false);

  const title = data?.title || "Curated Outfit Ensemble";
  const items = Array.isArray(data?.items) ? data.items : [];
  const comboDiscount = Number(data?.discount_percent || 15);
  const totalOriginalPrice = items.reduce((sum, it) => sum + (Number(it.price) || 0), 0);
  const comboPrice = data?.combo_price
    ? Number(data.combo_price)
    : Math.round(totalOriginalPrice * (1 - comboDiscount / 100));
  const savings = totalOriginalPrice - comboPrice;

  const handleAddEnsemble = () => {
    items.forEach((it) => {
      const finalId = it.id || it.product_id;
      if (finalId) {
        addToCart(
          {
            id: finalId,
            name: it.name || "Ensemble Item",
            price: it.price || 0,
            image_url: it.image_url || it.image,
            brand: it.brand || "DUKAAN",
          },
          1,
          it.size || "M",
          "Default"
        );
      }
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  if (items.length === 0) return null;

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-stone-900 via-stone-950 to-stone-900 text-white border border-stone-800 rounded-2xl p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-white/10">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-200">
          <Sparkles size={14} className="text-amber-400" />
          <span>{title}</span>
        </div>
        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/30">
          Save {comboDiscount}% Combo
        </span>
      </div>

      {/* Paired Garments (Side by Side with + in between) */}
      <div className="flex items-center justify-between gap-2 my-3">
        {items.map((it, idx) => {
          const finalId = it.id || it.product_id;
          const imgUrl =
            it.image_url ||
            it.image ||
            (finalId ? `https://picsum.photos/seed/${finalId}/300/300` : "https://picsum.photos/seed/dukaan/300/300");

          return (
            <React.Fragment key={`${finalId}-${idx}`}>
              <div className="flex-1 bg-white/5 border border-white/10 rounded-xl p-2 flex flex-col items-center text-center">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden bg-stone-800 mb-1.5">
                  <img src={imgUrl} alt={it.name} className="w-full h-full object-cover" />
                </div>
                <p className="text-[11px] font-semibold text-stone-200 line-clamp-1 w-full">
                  {it.name || "Look Item"}
                </p>
                <span className="text-[10px] font-bold text-amber-300 mt-0.5">
                  ₹{Number(it.price || 0).toLocaleString("en-IN")}
                </span>
              </div>
              {idx < items.length - 1 && (
                <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-amber-400 flex-shrink-0">
                  <Plus size={14} strokeWidth={3} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Bundle Pricing Bar */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-2.5 flex items-center justify-between mb-3 text-xs">
        <div>
          <span className="text-[10px] text-stone-400 uppercase tracking-wider block">Combo Price</span>
          <div className="flex items-baseline gap-2">
            <span className="text-base font-extrabold text-white">
              ₹{comboPrice.toLocaleString("en-IN")}
            </span>
            {totalOriginalPrice > comboPrice && (
              <span className="text-xs text-stone-400 line-through">
                ₹{totalOriginalPrice.toLocaleString("en-IN")}
              </span>
            )}
          </div>
        </div>

        {savings > 0 && (
          <div className="text-right">
            <span className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold block">
              Bundle Savings
            </span>
            <span className="text-xs font-bold text-emerald-400">
              -₹{savings.toLocaleString("en-IN")}
            </span>
          </div>
        )}
      </div>

      {/* Add Entire Look Button */}
      <button
        type="button"
        onClick={handleAddEnsemble}
        className={`w-full py-2.5 px-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md ${
          added
            ? "bg-emerald-600 text-white"
            : "bg-white hover:bg-stone-200 text-stone-900"
        }`}
      >
        {added ? (
          <>
            <Check size={14} strokeWidth={2.5} />
            <span>Complete Look Added to Bag!</span>
          </>
        ) : (
          <>
            <ShoppingBag size={14} />
            <span>Add Complete Look to Bag</span>
          </>
        )}
      </button>
    </div>
  );
}
