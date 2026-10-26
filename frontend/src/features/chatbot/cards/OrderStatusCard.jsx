import React from "react";
import { Package, Truck, CheckCircle2, Clock, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useStore } from "../../../store/useStore";

export function OrderStatusCard({ data }) {
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);
  const orderId = data?.order_id || "ORD-2026-9812";
  const status = (data?.status || "shipped").toLowerCase();
  const deliveryEstimate = data?.delivery_estimate || "Expected in 2-3 Days";
  const items = Array.isArray(data?.items) ? data.items : [];

  const steps = [
    { label: "Placed", done: true },
    { label: "Quality Check", done: status !== "placed" },
    { label: "Dispatched", done: status === "shipped" || status === "out_for_delivery" || status === "delivered" },
    { label: "Delivered", done: status === "delivered" },
  ];

  return (
    <div className="w-full mt-3 bg-white border border-stone-200/90 rounded-2xl p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-stone-100">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-900">
          <Package size={14} className="text-[#C45C26]" />
          <span>Live Order Tracking</span>
        </div>
        <span className="text-[10px] font-mono font-bold text-stone-600 bg-stone-100 px-2 py-0.5 rounded-full">
          #{orderId}
        </span>
      </div>

      {/* Progress Timeline Stepper */}
      <div className="my-3 px-1">
        <div className="flex items-center justify-between relative">
          <div className="absolute left-2 right-2 top-2 h-0.5 bg-stone-200 -z-0" />
          {steps.map((step, idx) => (
            <div key={idx} className="flex flex-col items-center relative z-10">
              <div
                className={`w-4.5 h-4.5 rounded-full flex items-center justify-center text-[10px] ${
                  step.done
                    ? "bg-emerald-600 text-white shadow-xs"
                    : "bg-white border-2 border-stone-300 text-stone-400"
                }`}
              >
                {step.done ? <CheckCircle2 size={12} /> : idx + 1}
              </div>
              <span className={`text-[10px] mt-1 font-semibold ${step.done ? "text-stone-900" : "text-stone-400"}`}>
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Delivery Estimate Box */}
      <div className="bg-stone-50 rounded-xl p-2.5 border border-stone-200/60 flex items-center justify-between text-xs my-3">
        <div className="flex items-center gap-2 text-stone-700">
          <Truck size={14} className="text-emerald-700" />
          <span className="font-medium">{deliveryEstimate}</span>
        </div>
        <span className="text-[10px] font-bold uppercase text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-md">
          {status}
        </span>
      </div>

      {/* View In Orders Button */}
      <Link
        to="/orders"
        onClick={() => setIsAgentOpen(false)}
        className="w-full py-2 px-3 rounded-xl bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors shadow-xs"
      >
        <span>View Full Order Details</span>
        <ArrowRight size={13} />
      </Link>
    </div>
  );
}
