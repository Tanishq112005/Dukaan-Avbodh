import React from "react";
import { ShoppingBag, ArrowRight, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useStore } from "../../../store/useStore";

export function CartUpdateCard({ data }) {
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const action = data?.action || "updated";
  const item = data?.item || {};
  const cartCount = data?.cart_count;
  const cartTotal = data?.cart_total;

  const actionLabel =
    action === "added"
      ? "Added to your shopping bag"
      : action === "removed"
      ? "Removed from your bag"
      : action === "cleared"
      ? "Shopping bag cleared"
      : "Shopping bag updated";

  return (
    <div className="w-full mt-3 bg-stone-50 border border-stone-200/90 rounded-2xl p-3.5 shadow-xs">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-stone-200/60">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-800">
          <CheckCircle2 size={13} className="text-emerald-600" />
          <span>{actionLabel}</span>
        </div>
        {cartCount !== undefined && (
          <span className="text-[11px] font-semibold text-stone-500">
            {cartCount} {cartCount === 1 ? "item" : "items"} in bag
          </span>
        )}
      </div>

      {item && (item.name || item.title) && (
        <div className="flex items-center gap-3 py-1">
          {item.image_url && (
            <div className="w-12 h-14 rounded-lg bg-stone-200 overflow-hidden flex-shrink-0 border border-stone-200">
              <img
                src={item.image_url}
                alt={item.name}
                className="w-full h-full object-cover"
              />
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

      {cartTotal !== undefined && cartTotal !== null && (
        <div className="mt-2.5 pt-2 border-t border-stone-200/60 flex items-center justify-between text-xs">
          <span className="text-stone-500">Cart Subtotal</span>
          <span className="font-bold text-stone-900">
            ₹{Number(cartTotal).toLocaleString("en-IN")}
          </span>
        </div>
      )}

      <div className="mt-3 flex gap-2">
        <Link
          to="/cart"
          onClick={() => setIsAgentOpen(false)}
          className="flex-1 py-2 px-3 rounded-xl bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-bold tracking-wider uppercase flex items-center justify-center gap-1.5 transition-colors"
        >
          <span>View Bag</span>
          <ArrowRight size={13} />
        </Link>
      </div>
    </div>
  );
}
