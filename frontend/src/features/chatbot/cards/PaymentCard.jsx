import React from "react";
import { ShieldCheck, ArrowRight, CheckCircle, CreditCard, Lock, ShoppingBag } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function PaymentCard({ data, onPayClick }) {
  const { openPaymentLink, pendingPayment, cart: storeCart } = useStore();
  const paymentUrl = data?.payment_link;
  const amount = data?.amount ? Number(data.amount) : null;
  const isPaid = data?.status === "paid" || pendingPayment?.notified;

  // Items being ordered: from backend card data or fallback to active cart
  const orderedItems = (Array.isArray(data?.cart) && data.cart.length > 0)
    ? data.cart
    : (Array.isArray(data?.cart_items) && data.cart_items.length > 0)
    ? data.cart_items
    : (Array.isArray(storeCart) ? storeCart : []);

  if (!paymentUrl && !isPaid) return null;

  const handlePay = () => {
    if (onPayClick) {
      onPayClick(paymentUrl);
    } else {
      openPaymentLink(paymentUrl);
    }
  };

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-stone-900 via-stone-850 to-stone-900 text-white rounded-2xl p-4 shadow-lg border border-stone-700/80">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-white/10">
        <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase text-stone-200">
          <CreditCard size={14} className="text-[#C45C26]" />
          <span>{data.title || "Order Summary & Checkout"}</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
          <Lock size={10} />
          <span>256-Bit SSL</span>
        </div>
      </div>

      {/* Cart Items Ordered Breakdown (Photos + Details) */}
      {orderedItems.length > 0 && (
        <div className="mb-3.5 bg-white/5 rounded-xl p-2.5 border border-white/10">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-2 px-1">
            <span>Items to be Ordered ({orderedItems.length})</span>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-1">
            {orderedItems.map((item, idx) => {
              const itemId = item.id || item.product_id;
              const imgUrl =
                item.image_url ||
                (itemId ? `https://picsum.photos/seed/${itemId}/200/250` : "https://picsum.photos/seed/dukaan/200/250");
              const price = item.price ? `₹${Number(item.price).toLocaleString("en-IN")}` : "₹0";

              return (
                <div
                  key={`${itemId}-${idx}`}
                  className="flex items-center gap-2.5 bg-white/5 rounded-lg p-1.5 border border-white/5"
                >
                  <div className="w-11 h-13 rounded-md bg-stone-800 overflow-hidden flex-shrink-0 border border-white/10">
                    <img
                      src={imgUrl}
                      alt={item.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h5 className="text-xs font-semibold text-stone-100 truncate">
                      {item.name || "Apparel Item"}
                    </h5>
                    <div className="flex items-center gap-2 text-[10px] text-stone-400 mt-0.5">
                      {item.size && <span>Size: <strong className="text-stone-200">{item.size}</strong></span>}
                      <span>Qty: <strong className="text-stone-200">{item.qty || item.quantity || 1}</strong></span>
                    </div>
                  </div>
                  <span className="font-bold text-xs text-stone-100">{price}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Total Amount */}
      <div className="bg-white/5 rounded-xl p-3 flex items-center justify-between mb-3 border border-white/10">
        <div>
          <span className="text-[10px] text-stone-400 uppercase tracking-wider block font-medium">
            Total Payable Amount
          </span>
          {amount !== null ? (
            <span className="font-display text-2xl font-extrabold text-white">
              ₹{amount.toLocaleString("en-IN")}
            </span>
          ) : (
            <span className="text-sm font-semibold text-white">Ready for Payment</span>
          )}
        </div>
        <div className="text-right">
          <span className="text-[10px] uppercase tracking-wider text-stone-400 block font-medium">
            Gateway
          </span>
          <span className="font-bold text-xs text-stone-200">Razorpay Secure</span>
        </div>
      </div>

      {isPaid ? (
        <div className="w-full py-2.5 px-3 rounded-xl bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-bold flex items-center justify-center gap-1.5">
          <CheckCircle size={15} className="text-emerald-400" />
          <span>Payment Verified & Confirmed</span>
        </div>
      ) : (
        <button
          type="button"
          onClick={handlePay}
          className="w-full py-3 px-4 rounded-xl bg-[#C45C26] hover:bg-[#a3481b] text-white text-xs font-bold tracking-wider uppercase flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg cursor-pointer"
        >
          <span>Pay Now Securely</span>
          <ArrowRight size={13} />
        </button>
      )}

      <div className="flex items-center justify-center gap-1.5 mt-2.5 text-[10px] text-stone-400">
        <ShieldCheck size={12} className="text-emerald-400" />
        <span>Backed by Dukaan Authenticity & Delivery Guarantee</span>
      </div>
    </div>
  );
}
