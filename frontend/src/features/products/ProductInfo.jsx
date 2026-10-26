import { useState } from "react";
import { Star, Minus, Plus, ShoppingBag, MessageCircle, Truck, RotateCcw, ShieldCheck, Check } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function ProductInfo({ product, addToCart }) {
  const [qty, setQty] = useState(1);
  const [selSize, setSelSize] = useState("Large");
  const [justAdded, setJustAdded] = useState(false);
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const sendAiMessage = useStore((state) => state.sendAiMessage);

  const productSizes = product.sizes
    ? product.sizes.split(",").map((s) => s.trim())
    : ["Small", "Medium", "Large", "X-Large"];

  const handleAdd = () => {
    addToCart(qty, selSize, "Default");
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1600);
  };

  const handleBargainWithAi = () => {
    setIsAgentOpen(true);
    sendAiMessage(`Can I get a VIP discount or combo deal on the ${product.name}?`);
  };

  const formattedPrice = product.price !== undefined && product.price !== null
    ? `₹${Number(product.price).toLocaleString("en-IN")}`
    : "₹0";

  const originalPrice = product.discount > 0 && product.price
    ? `₹${Math.round(Number(product.price) / (1 - product.discount / 100)).toLocaleString("en-IN")}`
    : null;

  return (
    <div className="md:w-1/2 flex flex-col justify-between py-2 space-y-6">
      {/* Brand & Title */}
      <div>
        <div className="flex items-center justify-between gap-3 mb-2">
          <p className="text-[#C45C26] font-bold uppercase tracking-[0.2em] text-xs">
            {product.brand || "ATELIER LUXURY"}
          </p>
          <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100">
            In Stock
          </span>
        </div>

        <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold uppercase text-stone-900 tracking-tight leading-snug">
          {product.name}
        </h1>

        {/* Rating & Reviews */}
        <div className="flex items-center gap-2 mt-3">
          <div className="flex text-amber-500">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                size={16}
                fill={i < Math.floor(product.rating || 4.5) ? "currentColor" : "none"}
                strokeWidth={i < Math.floor(product.rating || 4.5) ? 0 : 1.5}
                className="text-amber-500"
              />
            ))}
          </div>
          <span className="text-xs font-bold text-stone-800">{product.rating ? Number(product.rating).toFixed(1) : "4.5"}/5</span>
          <span className="text-xs text-stone-400">· 142 verified buyers</span>
        </div>

        {/* Pricing */}
        <div className="flex items-baseline gap-3 mt-5 pb-5 border-b border-stone-200/80">
          <span className="font-display text-3xl sm:text-4xl font-extrabold text-stone-900">
            {formattedPrice}
          </span>
          {originalPrice && (
            <span className="text-base text-stone-400 line-through font-medium">
              {originalPrice}
            </span>
          )}
          {product.discount > 0 && (
            <span className="bg-[#6e1423] text-white text-xs font-bold px-2.5 py-1 rounded-full tracking-wider">
              SAVE {product.discount}%
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-stone-600 text-sm leading-relaxed mt-4">
          {product.description ||
            "Crafted with exceptional tailoring from breathable organic luxury cotton blend. Designed for effortless draping and timeless elegance."}
        </p>
      </div>

      {/* Sizing Selector */}
      <div className="space-y-3 pt-2">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold uppercase tracking-wider text-stone-500">Select Size</span>
          <button
            onClick={() => {
              setIsAgentOpen(true);
              sendAiMessage(`What size should I get for ${product.name} if I am 5'10?`);
            }}
            className="text-[#6e1423] font-semibold hover:underline cursor-pointer"
          >
            Ask Stylist for Sizing advice
          </button>
        </div>

        <div className="flex flex-wrap gap-2.5">
          {productSizes.map((size) => (
            <button
              key={size}
              type="button"
              onClick={() => setSelSize(size)}
              className={`px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer ${
                selSize === size
                  ? "bg-stone-900 text-white shadow-sm"
                  : "bg-white border border-stone-200 text-stone-700 hover:border-stone-400 hover:bg-stone-50"
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Quantity & CTA Buttons */}
      <div className="space-y-3 pt-4 border-t border-stone-200/80">
        <div className="flex items-center gap-3">
          {/* Quantity stepper */}
          <div className="flex items-center justify-between bg-stone-100 rounded-2xl px-4 py-3 w-32 border border-stone-200">
            <button
              type="button"
              onClick={() => setQty(Math.max(1, qty - 1))}
              className="text-stone-600 hover:text-stone-900 p-1 cursor-pointer"
              title="Decrease quantity"
            >
              <Minus size={15} />
            </button>
            <span className="font-bold text-sm text-stone-900">{qty}</span>
            <button
              type="button"
              onClick={() => setQty(qty + 1)}
              className="text-stone-600 hover:text-stone-900 p-1 cursor-pointer"
              title="Increase quantity"
            >
              <Plus size={15} />
            </button>
          </div>

          {/* Add to Bag Button */}
          <Button
            onClick={handleAdd}
            className={`flex-1 rounded-2xl py-6.5 text-sm font-bold tracking-wider uppercase shadow-md transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer ${
              justAdded
                ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                : "bg-stone-900 hover:bg-[#6e1423] text-white"
            }`}
          >
            {justAdded ? (
              <>
                <Check size={18} strokeWidth={2.5} />
                <span>Added to Bag</span>
              </>
            ) : (
              <>
                <ShoppingBag size={18} />
                <span>Add to Bag</span>
              </>
            )}
          </Button>
        </div>

        {/* AI Negotiation & Stylist Button */}
        <button
          onClick={handleBargainWithAi}
          type="button"
          className="w-full py-3.5 px-4 rounded-2xl border-2 border-dashed border-[#C45C26]/50 hover:border-[#C45C26] bg-[#C45C26]/5 hover:bg-[#C45C26]/10 text-stone-900 transition-all text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer"
        >
          <MessageCircle size={15} className="text-[#C45C26]" />
          <span>Negotiate price or ask for combo discount with AI Stylist</span>
        </button>
      </div>

      {/* Trust Assurance Guarantee Points */}
      <div className="grid grid-cols-3 gap-2 pt-4 border-t border-stone-200/80 text-center">
        <div className="flex flex-col items-center gap-1 p-2">
          <Truck size={16} className="text-stone-500" />
          <span className="text-[11px] font-semibold text-stone-800">Free Express</span>
          <span className="text-[10px] text-stone-400">On all orders ₹999+</span>
        </div>
        <div className="flex flex-col items-center gap-1 p-2 border-x border-stone-200/60">
          <RotateCcw size={16} className="text-stone-500" />
          <span className="text-[11px] font-semibold text-stone-800">14-Day Returns</span>
          <span className="text-[10px] text-stone-400">Doorstep pickup</span>
        </div>
        <div className="flex flex-col items-center gap-1 p-2">
          <ShieldCheck size={16} className="text-stone-500" />
          <span className="text-[11px] font-semibold text-stone-800">100% Verified</span>
          <span className="text-[10px] text-stone-400">Authentic luxury</span>
        </div>
      </div>
    </div>
  );
}
