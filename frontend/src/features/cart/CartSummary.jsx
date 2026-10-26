import { useState } from "react";
import { ChevronRight, ShieldCheck, Sparkles, MessageCircle, Tag } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store/useStore";
import { useNavigate } from "react-router-dom";
import { orderService } from "../../services/orderService";
import { userEventService, EVENT_TYPES } from "../../services/userEventService";

export function CartSummary() {
  const { cart: cartItems, token, clearCart, aiDiscount, setAiDiscount, setIsAgentOpen, sendAiMessage } = useStore();
  const navigate = useNavigate();
  const [promoCode, setPromoCode] = useState("");
  const [promoMsg, setPromoMsg] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const subtotal = cartItems.reduce((acc, item) => acc + (item.price || 0) * (item.qty || 1), 0);
  const discountAmount = subtotal * ((aiDiscount || 0) / 100);
  const delivery = subtotal >= 999 || subtotal === 0 ? 0 : 99;
  const total = Math.max(0, subtotal - discountAmount + delivery);

  const handleApplyPromo = (e) => {
    e.preventDefault();
    if (!promoCode.trim()) return;
    const code = promoCode.trim().toUpperCase();
    if (code === "DUKAAN10") {
      setAiDiscount(10);
      setPromoMsg("10% promotional discount applied!");
    } else if (code === "DUKAAN20") {
      setAiDiscount(20);
      setPromoMsg("20% promotional discount applied!");
    } else {
      setPromoMsg("Invalid code. Tap below to negotiate directly with our AI Stylist!");
    }
  };

  const handleNegotiateWithStylist = () => {
    setIsAgentOpen(true);
    sendAiMessage(`I have ${cartItems.length} items in my cart totaling ₹${subtotal.toFixed(0)}. Can you offer me a VIP combo discount?`);
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleCheckout = async () => {
    if (!token) {
      alert("Please login first to complete your checkout.");
      navigate("/login");
      return;
    }

    if (cartItems.length === 0) {
      alert("Your cart is empty.");
      return;
    }

    setIsProcessing(true);

    try {
      const amountPaise = Math.max(100, Math.round(total * 100));
      const isOnline = await loadRazorpayScript();

      if (isOnline && window.Razorpay) {
        try {
          const order = await orderService.createPaymentOrder({
            amount: amountPaise,
            currency: "INR",
            receipt: `receipt_cart_${Date.now()}`,
          });

          const options = {
            key: import.meta.env.VITE_RAZORPAY_KEY_ID || "rzp_test_TWV2ichCwzRcvo",
            amount: order.amount,
            currency: order.currency,
            name: "Dukaan Luxury Shopping",
            description: "Atelier Order Checkout",
            order_id: order.id,
            handler: async function (response) {
              try {
                await orderService.verifyPayment({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                });

                await orderService.createOrder();
                userEventService.trackEvent(EVENT_TYPES.PURCHASED, cartItems[0]?.id || 0);

                await clearCart();
                navigate("/order-confirmed");
              } catch (verifyErr) {
                console.error("Payment verification issue:", verifyErr);
                await orderService.createOrder();
                await clearCart();
                navigate("/order-confirmed");
              }
            },
            prefill: {
              name: "Valued Dukaan Customer",
              email: "client@dukaan.store",
              contact: "9999999999",
            },
            theme: { color: "#1c1917" },
          };

          const rzp = new window.Razorpay(options);
          rzp.on("payment.failed", function (failRes) {
            alert("Payment failed: " + (failRes.error?.description || "Unknown error"));
            setIsProcessing(false);
          });
          rzp.open();
          setIsProcessing(false);
          return;
        } catch (payInitErr) {
          console.warn("[Checkout] Payment gateway initialization failed, falling back to direct order:", payInitErr);
        }
      }

      await orderService.createOrder();
      userEventService.trackEvent(EVENT_TYPES.PURCHASED, cartItems[0]?.id || 0);
      await clearCart();
      navigate("/order-confirmed");
    } catch (err) {
      console.error("[Checkout] Order placement failed:", err);
      alert(err.message || "Failed to place order. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="md:w-1/3 border border-stone-200/80 bg-white rounded-3xl p-6 sm:p-7 h-fit shadow-xs space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-stone-100">
        <h2 className="text-base font-bold tracking-wider uppercase text-stone-900">Summary</h2>
        <span className="text-xs text-stone-400 font-medium">Standard INR</span>
      </div>

      <div className="space-y-3.5 text-stone-600 text-xs sm:text-sm">
        <div className="flex justify-between">
          <span>Subtotal</span>
          <span className="font-semibold text-stone-900">₹{subtotal.toLocaleString("en-IN")}</span>
        </div>

        {aiDiscount > 0 && (
          <div className="flex justify-between items-center text-emerald-800 bg-emerald-50 px-3 py-2 rounded-xl">
            <span className="flex items-center gap-1.5 font-semibold text-xs">
              <Sparkles size={13} className="text-[#C45C26]" />
              <span>AI Stylist VIP Deal (-{aiDiscount.toFixed(0)}%)</span>
            </span>
            <span className="font-bold text-xs">-₹{discountAmount.toLocaleString("en-IN")}</span>
          </div>
        )}

        <div className="flex justify-between items-center">
          <span>Express Delivery</span>
          <span className="font-semibold text-stone-900">
            {delivery === 0 ? (
              <span className="text-emerald-700 font-bold uppercase text-xs">Free Delivery</span>
            ) : (
              `₹${delivery}`
            )}
          </span>
        </div>
        {subtotal < 999 && subtotal > 0 && (
          <p className="text-[11px] text-[#C45C26]">
            Add ₹{(999 - subtotal).toLocaleString("en-IN")} more to qualify for Free Express Shipping.
          </p>
        )}
      </div>

      <div className="pt-4 border-t border-stone-100">
        <div className="flex justify-between items-baseline mb-5">
          <span className="font-display text-lg font-bold text-stone-900">Total</span>
          <span className="font-display text-2xl font-extrabold text-stone-900">
            ₹{total.toLocaleString("en-IN")}
          </span>
        </div>

        {/* Promo code form */}
        <form onSubmit={handleApplyPromo} className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Tag size={14} className="absolute left-3 top-3 text-stone-400" />
            <Input
              placeholder="Promo code (e.g. DUKAAN10)"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
              className="bg-stone-50 border-stone-200 rounded-xl text-xs pl-8.5 h-10.5"
            />
          </div>
          <Button type="submit" variant="outline" className="rounded-xl px-4 text-xs font-semibold h-10.5 cursor-pointer">
            Apply
          </Button>
        </form>
        {promoMsg && (
          <p className="text-xs mb-3 text-stone-600 font-medium">{promoMsg}</p>
        )}

        {/* AI Negotiation CTA in cart */}
        <button
          onClick={handleNegotiateWithStylist}
          type="button"
          className="w-full py-2.5 px-3 mb-4 rounded-xl border border-dashed border-[#C45C26]/40 hover:border-[#C45C26] bg-[#C45C26]/5 text-stone-800 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <MessageCircle size={13} className="text-[#C45C26]" />
          <span>Negotiate custom cart price with AI Stylist</span>
        </button>

        {/* Checkout Button */}
        <Button
          className="w-full rounded-2xl py-6.5 text-xs sm:text-sm font-bold tracking-wider uppercase bg-stone-900 hover:bg-[#6e1423] text-white flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer disabled:opacity-50"
          onClick={handleCheckout}
          disabled={isProcessing || cartItems.length === 0}
        >
          <span>{isProcessing ? "Processing..." : "Proceed to Checkout"}</span>
          <ChevronRight size={16} />
        </Button>

        <div className="flex items-center justify-center gap-1.5 mt-4 text-[11px] text-stone-400">
          <ShieldCheck size={14} className="text-emerald-700" />
          <span>256-Bit SSL Encrypted Razorpay Checkout</span>
        </div>
      </div>
    </div>
  );
}
