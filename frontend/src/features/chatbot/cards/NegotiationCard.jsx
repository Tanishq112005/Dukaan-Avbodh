import React, { useState } from "react";
import { Tag, Check, Sparkles, MessageCircle, ArrowRight } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function NegotiationCard({ data, onAction }) {
  const { setAiDiscount, sendAiMessage } = useStore();
  const [isAccepted, setIsAccepted] = useState(data.status === "accepted");

  const discountPercent = Number(data?.discount_percent || 0);
  const offerPrice = data?.offer_price ? Number(data.offer_price) : null;
  const originalPrice = data?.original_price ? Number(data.original_price) : null;
  const savings = data?.savings ? Number(data.savings) : (originalPrice && offerPrice ? originalPrice - offerPrice : null);
  const comboOffer = data?.combo_offer;

  const handleAccept = () => {
    setIsAccepted(true);
    if (onAction) {
      onAction("accept_offer", { discountPercent, offerPrice, product_id: data.product_id });
    } else if (data.product_name) {
      if (data.in_cart) {
        sendAiMessage(`Deal accepted on ${data.product_name}! Please apply the ${discountPercent}% discount to my bag.`);
      } else {
        sendAiMessage(`Deal accepted! Please add ${data.product_name} to my bag at ₹${offerPrice} (${discountPercent}% off).`);
      }
    } else {
      sendAiMessage(`Deal accepted! Please proceed with the ${discountPercent}% discount.`);
    }
  };

  const handleCounter = () => {
    if (data.product_name) {
      sendAiMessage(`Can you offer a slightly better deal on ${data.product_name}?`);
    } else {
      sendAiMessage(`Can you offer an extra 5% off if I checkout immediately?`);
    }
  };

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-amber-50/70 via-stone-50 to-orange-50/40 border border-amber-200/90 rounded-2xl p-4 shadow-xs">
      {/* Top Banner */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-amber-200/50">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-900">
          <Sparkles size={14} className="text-[#C45C26]" />
          <span>{data.product_name ? `${data.product_name}` : (data.title || "VIP Exclusive Bargain")}</span>
        </div>
        <span className="bg-[#C45C26] text-white text-[10px] font-bold uppercase px-2 py-0.5 rounded-full tracking-wider shadow-xs">
          {discountPercent}% OFF
        </span>
      </div>

      {/* Pricing Comparison */}
      <div className="bg-white/90 border border-stone-200/80 rounded-xl p-3 flex items-center justify-between mb-3">
        <div>
          <span className="text-[11px] text-stone-500 font-medium block">
            Exclusive Deal Price
          </span>
          <div className="flex items-baseline gap-2 mt-0.5">
            {offerPrice !== null ? (
              <span className="font-display text-xl font-extrabold text-stone-900">
                ₹{offerPrice.toLocaleString("en-IN")}
              </span>
            ) : (
              <span className="font-display text-lg font-bold text-stone-900">
                {discountPercent}% Discount Applied
              </span>
            )}
            {originalPrice !== null && (
              <span className="text-xs text-stone-400 line-through">
                ₹{originalPrice.toLocaleString("en-IN")}
              </span>
            )}
          </div>
        </div>

        {savings !== null && savings > 0 && (
          <div className="text-right">
            <span className="text-[10px] uppercase tracking-wider text-emerald-700 font-bold block">
              You Save
            </span>
            <span className="font-bold text-sm text-emerald-700">
              ₹{savings.toLocaleString("en-IN")}
            </span>
          </div>
        )}
      </div>

      {/* Combo items if present */}
      {comboOffer?.items && comboOffer.items.length > 0 && (
        <div className="mb-3 p-2 bg-amber-100/40 rounded-lg text-xs text-amber-900">
          <span className="font-semibold">Bundle includes: </span>
          {comboOffer.items.map((it) => it.name || it).join(" + ")}
        </div>
      )}

      {/* Actions */}
      {isAccepted ? (
        <div className="w-full py-2 px-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center justify-center gap-1.5">
          <Check size={14} className="text-emerald-600" />
          <span>{data.product_name ? (data.in_cart ? `Discount Applied to ${data.product_name}` : `Special Price Agreed for ${data.product_name}`) : "Discount Applied to Your Shopping Bag"}</span>
        </div>
      ) : (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleAccept}
            className="flex-1 py-2.5 px-3 rounded-xl bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 transition-all shadow-xs cursor-pointer"
          >
            <Check size={13} />
            <span>Accept Deal</span>
          </button>
          <button
            type="button"
            onClick={handleCounter}
            className="py-2.5 px-3 rounded-xl bg-white border border-stone-300 hover:border-stone-400 text-stone-700 text-xs font-semibold flex items-center justify-center gap-1 transition-colors cursor-pointer"
          >
            <MessageCircle size={13} />
            <span>Counter</span>
          </button>
        </div>
      )}
    </div>
  );
}
