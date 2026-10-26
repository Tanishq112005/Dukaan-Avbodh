import { useState, useMemo } from "react";
import { Star, Minus, Plus, ShoppingBag, Sparkles, Truck, RotateCcw, ShieldCheck, Check } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

// Helper to extract clean editorial prose and key-value specs from raw descriptions
function parseProductDetails(desc, product) {
  if (!desc) {
    return {
      editorial: "Crafted with exceptional tailoring from breathable organic luxury cotton blend. Designed for effortless draping and timeless elegance.",
      specs: [
        { label: "Fit", value: "Regular" },
        { label: "Fabric", value: "Luxury Cotton" },
        { label: "Occasion", value: "Casual & Evening" },
      ],
    };
  }

  const keyPattern = /([A-Za-z\s]+):\s*([^.]+)\./g;
  const specs = [];
  let match;
  let lastIndex = 0;

  while ((match = keyPattern.exec(desc)) !== null) {
    const rawKey = match[1].trim();
    const rawVal = match[2].trim();
    lastIndex = keyPattern.lastIndex;

    const lowerKey = rawKey.toLowerCase();
    if (lowerKey !== "brand" && lowerKey !== "full name") {
      specs.push({
        label: rawKey.replace(" Type", ""),
        value: rawVal,
      });
    }
  }

  let editorial = desc.slice(lastIndex).trim();
  if (!editorial || editorial.length < 15) {
    editorial = desc;
  }

  if (specs.length === 0) {
    if (product?.type) specs.push({ label: "Category", value: product.type });
    if (product?.brand) specs.push({ label: "Brand", value: product.brand });
    specs.push({ label: "Fit", value: "Regular" });
    specs.push({ label: "Care", value: "Machine Wash" });
  }

  return { editorial, specs: specs.slice(0, 6) };
}

export function ProductInfo({ product, addToCart }) {
  const [qty, setQty] = useState(1);
  const [selSize, setSelSize] = useState("Large");
  const [justAdded, setJustAdded] = useState(false);
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const sendAiMessage = useStore((state) => state.sendAiMessage);

  const productSizes = product.sizes
    ? product.sizes.split(",").map((s) => s.trim())
    : ["Small", "Medium", "Large", "X-Large"];

  const { editorial, specs } = useMemo(
    () => parseProductDetails(product.description, product),
    [product.description, product]
  );

  const handleAdd = () => {
    addToCart(qty, selSize, "Default");
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1600);
  };

  const handleBargainWithAi = () => {
    setIsAgentOpen(true);
    sendAiMessage(`Can I get a VIP discount or combo deal on the ${product.name}?`);
  };

  // Base list / selling price matching catalog card
  const displayPrice =
    product.discount > 0 && product.price
      ? `₹${Math.round(Number(product.price) / (1 - product.discount / 100)).toLocaleString("en-IN")}`
      : product.price !== undefined && product.price !== null
      ? `₹${Number(product.price).toLocaleString("en-IN")}`
      : "₹0";

  return (
    <div className="w-full flex flex-col justify-between space-y-4">
      {/* Brand & Stock Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[#C45C26] font-extrabold uppercase tracking-[0.2em] text-[11px]">
            {product.brand || "ATELIER LUXURY"}
          </span>
          <span className="text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
            In Stock
          </span>
        </div>

        {/* Product Title */}
        <h1 className="font-display text-xl sm:text-2xl font-bold uppercase text-stone-900 tracking-tight leading-snug">
          {product.name}
        </h1>

        {/* Rating & Reviews */}
        <div className="flex items-center gap-1.5 mt-2">
          <div className="flex text-amber-500">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                size={13}
                fill={i < Math.floor(product.rating || 4.5) ? "currentColor" : "none"}
                strokeWidth={i < Math.floor(product.rating || 4.5) ? 0 : 1.5}
                className="text-amber-500"
              />
            ))}
          </div>
          <span className="text-xs font-bold text-stone-800">
            {product.rating ? Number(product.rating).toFixed(1) : "4.5"}/5
          </span>
          <span className="text-[11px] text-stone-400">· 142 verified buyers</span>
        </div>

        {/* Pricing: Clean single price */}
        <div className="flex items-baseline gap-2 mt-3 pb-3 border-b border-stone-200/70">
          <span className="font-display text-2xl sm:text-3xl font-extrabold text-stone-900">
            {displayPrice}
          </span>
          <span className="text-[11px] text-stone-400 font-medium">
            (MRP inclusive of all taxes)
          </span>
        </div>

        {/* Description: Clean editorial text */}
        <p className="text-stone-600 text-xs sm:text-sm leading-relaxed mt-3">
          {editorial}
        </p>

        {/* Specifications Grid */}
        {specs.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-3.5 pt-3 border-t border-stone-150">
            {specs.map(({ label, value }, idx) => (
              <div
                key={idx}
                className="bg-stone-50 border border-stone-200/60 rounded-lg px-2.5 py-1.5 flex flex-col justify-center"
              >
                <span className="text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  {label}
                </span>
                <span className="text-xs font-semibold text-stone-800 truncate">
                  {value}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sizing Selector */}
      <div className="space-y-2 pt-1">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold uppercase tracking-wider text-stone-500 text-[11px]">
            Select Size
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {productSizes.map((size) => (
            <button
              key={size}
              type="button"
              onClick={() => setSelSize(size)}
              className={`min-w-[42px] h-9 px-3 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer ${
                selSize === size
                  ? "bg-stone-900 text-white shadow-xs"
                  : "bg-white border border-stone-200 text-stone-700 hover:border-stone-400 hover:bg-stone-50"
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Quantity & CTA Buttons */}
      <div className="space-y-2.5 pt-3 border-t border-stone-200/70">
        <div className="flex items-center gap-2.5">
          {/* Compact Quantity Stepper */}
          <div className="flex items-center justify-between bg-stone-100 rounded-xl px-3 h-10.5 w-28 border border-stone-200/80">
            <button
              type="button"
              onClick={() => setQty(Math.max(1, qty - 1))}
              className="text-stone-600 hover:text-stone-900 p-1 cursor-pointer"
              title="Decrease quantity"
            >
              <Minus size={14} />
            </button>
            <span className="font-bold text-xs text-stone-900">{qty}</span>
            <button
              type="button"
              onClick={() => setQty(qty + 1)}
              className="text-stone-600 hover:text-stone-900 p-1 cursor-pointer"
              title="Increase quantity"
            >
              <Plus size={14} />
            </button>
          </div>

          {/* Add to Bag Button */}
          <Button
            onClick={handleAdd}
            className={`flex-1 h-10.5 rounded-xl text-xs font-bold tracking-wider uppercase shadow-xs transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer ${
              justAdded
                ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                : "bg-stone-900 hover:bg-[#6e1423] text-white"
            }`}
          >
            {justAdded ? (
              <>
                <Check size={15} strokeWidth={2.5} />
                <span>Added to Bag</span>
              </>
            ) : (
              <>
                <ShoppingBag size={15} />
                <span>Add to Bag</span>
              </>
            )}
          </Button>
        </div>

        {/* AI Negotiation & Stylist Card */}
        <button
          onClick={handleBargainWithAi}
          type="button"
          className="w-full py-2.5 px-3 rounded-xl border border-amber-200/80 bg-gradient-to-r from-amber-50/70 via-stone-50 to-orange-50/50 hover:border-[#C45C26]/50 transition-all text-xs font-medium text-stone-800 flex items-center justify-between group cursor-pointer shadow-2xs"
        >
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[#C45C26] group-hover:rotate-12 transition-transform" />
            <span className="font-semibold text-stone-800 group-hover:text-[#6e1423] transition-colors">
              Negotiate price or ask for combo discount with AI Stylist
            </span>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#6e1423] bg-white border border-[#6e1423]/20 px-2 py-0.5 rounded-md shadow-2xs">
            Bargain
          </span>
        </button>
      </div>

      {/* Trust Assurance Guarantee Points */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-stone-200/70 text-center">
        <div className="flex flex-col items-center gap-0.5 p-1.5">
          <Truck size={14} className="text-stone-500 mb-0.5" />
          <span className="text-[10px] sm:text-[11px] font-semibold text-stone-800">Free Express</span>
          <span className="text-[9px] text-stone-400">On all orders ₹999+</span>
        </div>
        <div className="flex flex-col items-center gap-0.5 p-1.5 border-x border-stone-200/60">
          <RotateCcw size={14} className="text-stone-500 mb-0.5" />
          <span className="text-[10px] sm:text-[11px] font-semibold text-stone-800">14-Day Returns</span>
          <span className="text-[9px] text-stone-400">Doorstep pickup</span>
        </div>
        <div className="flex flex-col items-center gap-0.5 p-1.5">
          <ShieldCheck size={14} className="text-stone-500 mb-0.5" />
          <span className="text-[10px] sm:text-[11px] font-semibold text-stone-800">100% Verified</span>
          <span className="text-[9px] text-stone-400">Authentic luxury</span>
        </div>
      </div>
    </div>
  );
}
