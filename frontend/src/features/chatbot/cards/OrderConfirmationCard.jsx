import React from "react";
import { CheckCircle, PackageCheck, ArrowRight, Truck } from "lucide-react";
import { Link } from "react-router-dom";
import { useStore } from "../../../store/useStore";

export function OrderConfirmationCard({ data }) {
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const orderId = data?.order_id || "CONFIRMED";
  const amount = data?.amount ? Number(data.amount) : null;
  const deliveryEstimate = data?.delivery_estimate || "3-5 Business Days";

  return (
    <div className="w-full mt-3 bg-emerald-50/80 border border-emerald-200/90 rounded-2xl p-4 shadow-xs">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 flex-shrink-0">
          <CheckCircle size={18} />
        </div>
        <div>
          <h4 className="font-bold text-xs uppercase tracking-wider text-emerald-900">
            {data.title || "Order Placed Successfully"}
          </h4>
          <span className="text-[11px] text-emerald-700 font-medium">
            Order #{orderId}
          </span>
        </div>
      </div>

      <div className="bg-white/90 border border-emerald-100 rounded-xl p-3 space-y-2 mb-3 text-xs">
        <div className="flex items-center justify-between text-stone-600">
          <span className="flex items-center gap-1.5">
            <Truck size={13} className="text-emerald-700" />
            <span>Estimated Delivery</span>
          </span>
          <span className="font-semibold text-stone-900">{deliveryEstimate}</span>
        </div>

        {amount !== null && (
          <div className="flex items-center justify-between text-stone-600 pt-1 border-t border-stone-100">
            <span>Amount Paid</span>
            <span className="font-bold text-stone-900">
              ₹{amount.toLocaleString("en-IN")}
            </span>
          </div>
        )}
      </div>

      <Link
        to="/orders"
        onClick={() => setIsAgentOpen(false)}
        className="w-full py-2.5 px-3 rounded-xl bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors shadow-xs"
      >
        <PackageCheck size={14} />
        <span>View Order Details</span>
      </Link>
    </div>
  );
}
