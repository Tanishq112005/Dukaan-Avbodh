import React, { useState } from "react";
import { ShieldCheck, ExternalLink, CheckCircle, CreditCard, Lock } from "lucide-react";
import { useStore } from "../../../store/useStore";

export function PaymentCard({ data, onPayClick }) {
  const { openPaymentLink, pendingPayment } = useStore();
  const paymentUrl = data?.payment_link;
  const amount = data?.amount ? Number(data.amount) : null;
  const isPaid = data?.status === "paid" || pendingPayment?.notified;

  if (!paymentUrl && !isPaid) return null;

  const handlePay = () => {
    if (onPayClick) {
      onPayClick(paymentUrl);
    } else {
      openPaymentLink(paymentUrl);
    }
  };

  return (
    <div className="w-full mt-3 bg-gradient-to-br from-stone-900 to-stone-800 text-white rounded-2xl p-4 shadow-md border border-stone-700/80">
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-white/10">
        <div className="flex items-center gap-1.5 text-xs font-bold tracking-wider uppercase text-stone-200">
          <CreditCard size={14} className="text-[#C45C26]" />
          <span>{data.title || "Instant Checkout"}</span>
        </div>
        <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
          <Lock size={10} />
          <span>256-Bit SSL</span>
        </div>
      </div>

      <div className="bg-white/5 rounded-xl p-3 flex items-center justify-between mb-3 border border-white/10">
        <div>
          <span className="text-[11px] text-stone-400 uppercase tracking-wider block font-medium">
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
          <ExternalLink size={13} />
        </button>
      )}

      <div className="flex items-center justify-center gap-1.5 mt-2.5 text-[10px] text-stone-400">
        <ShieldCheck size={12} className="text-emerald-400" />
        <span>Backed by Dukaan Authenticity & Delivery Guarantee</span>
      </div>
    </div>
  );
}
