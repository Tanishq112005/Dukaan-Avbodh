import { useState } from "react";
import { ChevronRight, ShieldCheck } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store/useStore";
import { useNavigate } from "react-router-dom";
import { orderService } from "../../services/orderService";
import { userEventService, EVENT_TYPES } from "../../services/userEventService";

export function CartSummary() {
  const { cart: cartItems, token, clearCart, aiDiscount, setAiDiscount } = useStore();
  const navigate = useNavigate();
  const [promoCode, setPromoCode] = useState("");
  const [promoMsg, setPromoMsg] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const subtotal = cartItems.reduce((acc, item) => acc + (item.price || 0) * (item.qty || 1), 0);
  const discountAmount = subtotal * ((aiDiscount || 0) / 100);
  const delivery = subtotal > 0 ? 15 : 0;
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
      setPromoMsg("Invalid promo code. Chat with our AI Stylist to negotiate your best deal!");
    }
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
          // Attempt online payment creation
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

                // Place final order in DB
                await orderService.createOrder();
                userEventService.trackEvent(EVENT_TYPES.PURCHASED, cartItems[0]?.id || 0);

                await clearCart();
                navigate("/order-confirmed");
              } catch (verifyErr) {
                console.error("Payment verification failed:", verifyErr);
                alert("Payment verification issue on server, but creating your order...");
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

      // Fallback direct order creation (e.g. cash on delivery or dev test mode)
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
    <div className="md:w-1/3 border border-stone-200 bg-white rounded-[24px] p-6 h-fit shadow-sm">
      <h2 className="text-xl font-bold mb-6 text-stone-900">Order Summary</h2>
      <div className="space-y-4 text-stone-600 mb-6 text-sm">
        <div className="flex justify-between">
          <span>Subtotal</span>
          <span className="font-semibold text-stone-900">₹{subtotal.toFixed(0)}</span>
        </div>
        {aiDiscount > 0 && (
          <div className="flex justify-between text-emerald-700">
            <span>Special AI Discount (-{aiDiscount.toFixed(1)}%)</span>
            <span className="font-semibold">-₹{discountAmount.toFixed(0)}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Delivery Fee</span>
          <span className="font-semibold text-stone-900">
            {subtotal > 0 ? `₹${delivery}` : "₹0"}
          </span>
        </div>
      </div>

      <hr className="my-4 border-stone-200" />

      <div className="flex justify-between text-xl font-bold mb-6 text-stone-900">
        <span>Total</span>
        <span>₹{total.toFixed(0)}</span>
      </div>

      <form onSubmit={handleApplyPromo} className="flex gap-2 mb-2">
        <Input
          placeholder="Promo code (e.g. DUKAAN10)"
          value={promoCode}
          onChange={(e) => setPromoCode(e.target.value)}
          className="bg-[#EFE8DE] border-none rounded-full text-xs"
        />
        <Button type="submit" variant="outline" className="rounded-full px-5 text-xs">
          Apply
        </Button>
      </form>
      {promoMsg && (
        <p className="text-xs mb-4 text-stone-600 italic">{promoMsg}</p>
      )}

      <Button
        className="w-full rounded-full py-6 text-base bg-stone-900 hover:bg-stone-800 text-white flex items-center justify-center gap-2"
        onClick={handleCheckout}
        disabled={isProcessing || cartItems.length === 0}
      >
        <span>{isProcessing ? "Processing Order..." : "Proceed to Checkout"}</span>
        <ChevronRight className="w-5 h-5" />
      </Button>

      <div className="flex items-center justify-center gap-1.5 mt-4 text-xs text-stone-400">
        <ShieldCheck className="w-4 h-4 text-stone-500" />
        <span>Secure transaction backed by Dukaan Guarantee</span>
      </div>
    </div>
  );
}
