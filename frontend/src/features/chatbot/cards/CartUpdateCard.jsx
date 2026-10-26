import React from "react";
import { ShoppingBag, ArrowRight, CheckCircle2, ChevronRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../../../store/useStore";

export function CartUpdateCard({ data, onProductClick }) {
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const navigate = useNavigate();
  const action = data?.action || "updated";
  const item = data?.item;
  const cartList = Array.isArray(data?.cart) ? data.cart : [];
  const isViewAll = action === "view" || (cartList.length > 0 && !item);
  const cartCount = data?.cart_count !== undefined ? data.cart_count : cartList.length;
  const cartTotal = data?.cart_total;

  const actionLabel =
    isViewAll
      ? "Your Shopping Bag"
      : action === "added"
      ? "Added to your shopping bag"
      : action === "removed"
      ? "Removed from your bag"
      : action === "cleared"
      ? "Shopping bag cleared"
      : "Shopping bag updated";

  const handleProductNavigate = (p) => {
    const finalId = p.id || p.product_id;
    if (finalId) {
      navigate(`/product/${finalId}`);
      if (onProductClick) onProductClick(p);
    }
  };

  return (
    <div className="w-full mt-3 bg-stone-50 border border-stone-200/90 rounded-2xl p-3.5 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-stone-200/60">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-800">
          <ShoppingBag size={13} className="text-[#C45C26]" />
          <span>{actionLabel}</span>
        </div>
        <span className="text-[11px] font-semibold text-stone-500">
          {cartCount} {cartCount === 1 ? "item" : "items"}
        </span>
      </div>

      {/* Case 1: Full Cart View with photos of all items in cart */}
      {isViewAll && cartList.length > 0 && (
        <div className="space-y-2 max-h-56 overflow-y-auto custom-scrollbar my-2 pr-1">
          {cartList.map((cartItem, idx) => {
            const finalId = cartItem.id || cartItem.product_id;
            const imgUrl =
              cartItem.image_url ||
              (finalId ? `https://picsum.photos/seed/${finalId}/200/250` : "https://picsum.photos/seed/dukaan/200/250");
            const price = cartItem.price !== undefined ? `₹${Number(cartItem.price).toLocaleString("en-IN")}` : "₹0";

            return (
              <div
                key={`${finalId}-${idx}`}
                className="flex items-center gap-2.5 bg-white border border-stone-200/80 rounded-xl p-2 hover:border-stone-300 transition-colors"
              >
                <Link
                  to={`/product/${finalId}`}
                  onClick={() => onProductClick?.(cartItem)}
                  className="w-12 h-14 rounded-lg bg-stone-100 overflow-hidden flex-shrink-0 border border-stone-200/80 cursor-pointer block"
                >
                  <img
                    src={imgUrl}
                    alt={cartItem.name}
                    className="w-full h-full object-cover"
                  />
                </Link>
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/product/${finalId}`}
                    onClick={() => onProductClick?.(cartItem)}
                    className="font-semibold text-xs text-stone-900 truncate block hover:text-[#C45C26] transition-colors"
                  >
                    {cartItem.name || "Apparel Item"}
                  </Link>
                  <div className="flex items-center gap-2 mt-0.5 text-[11px] text-stone-500">
                    {cartItem.size && <span>Size: <strong className="text-stone-700">{cartItem.size}</strong></span>}
                    <span>Qty: <strong className="text-stone-700">{cartItem.qty || cartItem.quantity || 1}</strong></span>
                  </div>
                </div>
                <span className="font-bold text-xs text-stone-900">{price}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Case 2: Empty cart view */}
      {isViewAll && cartList.length === 0 && (
        <div className="py-4 text-center text-xs text-stone-500">
          Your shopping bag is currently empty.
        </div>
      )}

      {/* Case 3: Single Item Added/Removed/Updated */}
      {!isViewAll && item && (item.name || item.title) && (
        <div className="flex items-center gap-3 py-1 bg-white border border-stone-200/80 rounded-xl p-2 my-1">
          {item.image_url ? (
            <div className="w-12 h-14 rounded-lg bg-stone-100 overflow-hidden flex-shrink-0 border border-stone-200">
              <img
                src={item.image_url}
                alt={item.name}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="w-12 h-14 rounded-lg bg-stone-200 flex items-center justify-center text-stone-500 flex-shrink-0">
              <ShoppingBag size={18} />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-xs text-stone-900 truncate">
              {item.name || item.title}
            </h4>
            <div className="flex items-center gap-2 mt-0.5 text-[11px] text-stone-500">
              {item.size && <span>Size: <strong className="text-stone-700">{item.size}</strong></span>}
              {item.qty && <span>Qty: <strong className="text-stone-700">{item.qty}</strong></span>}
              {item.price !== undefined && (
                <span className="font-bold text-stone-900">₹{Number(item.price).toLocaleString("en-IN")}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cart Subtotal */}
      {cartTotal !== undefined && cartTotal !== null && (
        <div className="mt-2.5 pt-2 border-t border-stone-200/60 flex items-center justify-between text-xs">
          <span className="text-stone-500">Cart Total</span>
          <span className="font-bold text-stone-900">
            ₹{Number(cartTotal).toLocaleString("en-IN")}
          </span>
        </div>
      )}

      {/* Action CTA */}
      <div className="mt-3 flex gap-2">
        <Link
          to="/cart"
          onClick={() => setIsAgentOpen(false)}
          className="flex-1 py-2 px-3 rounded-xl bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-bold tracking-wider uppercase flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <span>View Bag & Checkout</span>
          <ArrowRight size={13} />
        </Link>
      </div>
    </div>
  );
}
