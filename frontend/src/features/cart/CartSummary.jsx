import { useState } from "react";
import { ChevronRight, ShieldCheck, AlertCircle } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store/useStore";
import { useNavigate } from "react-router-dom";
import { orderService } from "../../services/orderService";
import { userEventService, EVENT_TYPES } from "../../services/userEventService";

export function CartSummary() {
  const { cart: cartItems, token, clearCart, aiDiscount, setAiDiscount, user } = useStore();
  const navigate = useNavigate();
  const [promoCode, setPromoCode] = useState("");
  const [promoMsg, setPromoMsg] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const subtotal = cartItems.reduce((acc, item) => acc + (Number(item.price || 0)) * (item.qty || 1), 0);
  const originalSubtotal = cartItems.reduce((acc, item) => {
    const discPct = Number(item.discount_percentage || 0);
    const curr = Number(item.price || 0);
    const rawOrig = Number(item.original_price || 0);
    const orig = rawOrig > curr ? rawOrig : (discPct > 0 ? Math.round(curr / (1 - discPct / 100)) : curr);
    return acc + orig * (item.qty || 1);
  }, 0);
  const itemsDiscountAmount = Math.max(0, originalSubtotal - subtotal);
  const delivery = subtotal > 0 ? 15 : 0;
  const total = Math.max(0, subtotal + delivery);

  const handleApplyPromo = (e) => {
    e.preventDefault();
    if (!promoCode.trim()) return;
    const code = promoCode.trim().toUpperCase();
    if (code === "DUKAAN10") {
      setAiDiscount(10);
      setPromoMsg("10% promotional discount applied!");
      setErrorMessage("");
    } else if (code === "DUKAAN20") {
      setAiDiscount(20);
      setPromoMsg("20% promotional discount applied!");
      setErrorMessage("");
    } else {
      setPromoMsg("Invalid promo code. Chat with our AI Stylist to negotiate your best deal!");
    }
  };

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handleCheckout = async () => {
    setErrorMessage("");
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
      // 1. Concurrency-Locked Checkout: reserves inventory and creates payment order atomically
      const checkoutData = await orderService.checkoutWithLock({
        discount_percentage: aiDiscount || 0,
        customer_name: user?.name,
        customer_email: user?.email,
      });

      const isOnline = await loadRazorpayScript();

      if (isOnline && window.Razorpay && checkoutData.gateway_order_id) {
        const options = {
          key: checkoutData.client_key_id || import.meta.env.VITE_RAZORPAY_KEY_ID || "rzp_test_TWV2ichCwzRcvo",
          amount: checkoutData.amount_paise,
          currency: checkoutData.currency || "INR",
          name: "Dukaan Luxury Shopping",
          description: `Order Checkout (#${checkoutData.order_ids?.[0] || ""})`,
          order_id: checkoutData.gateway_order_id,
          handler: async function (response) {
            try {
              // 2. Cryptographic signature verification and order confirmation
              await orderService.verifyPayment({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                order_ids: checkoutData.order_ids,
              });

              userEventService.trackEvent(EVENT_TYPES.PURCHASED, cartItems[0]?.id || 0);
              await clearCart();
              navigate("/order-confirmed", {
                state: {
                  orderIds: checkoutData.order_ids,
                  total: checkoutData.total_amount,
                  paymentId: response.razorpay_payment_id,
                },
              });
            } catch (verifyErr) {
              console.error("[Checkout] Payment verification failed:", verifyErr);
              setErrorMessage("Payment verification issue on server. Please check your orders page.");
            }
          },
          prefill: {
            name: user?.name || "Valued Dukaan Customer",
            email: user?.email || "client@dukaan.store",
            contact: user?.phone || "",
          },
          theme: { color: "#1c1917" },
          modal: {
            ondismiss: function () {
              setIsProcessing(false);
            },
          },
        };

        const rzp = new window.Razorpay(options);
        rzp.on("payment.failed", function (failRes) {
          console.warn("[Checkout] Payment failed:", failRes);
          setErrorMessage("Payment failed: " + (failRes.error?.description || "Transaction cancelled"));
          setIsProcessing(false);
        });
        rzp.open();
        return;
      }

      // If Razorpay SDK could not load (e.g. offline dev), finalize order directly
      userEventService.trackEvent(EVENT_TYPES.PURCHASED, cartItems[0]?.id || 0);
      await clearCart();
      navigate("/order-confirmed", {
        state: {
          orderIds: checkoutData.order_ids,
          total: checkoutData.total_amount,
        },
      });
    } catch (err) {
      console.error("[Checkout] Order placement failed:", err);
      const detail = err.response?.data?.detail || err.message || "Failed to place order. Please try again.";
      setErrorMessage(detail);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="md:w-1/3 border border-stone-200 bg-white rounded-[24px] p-6 h-fit shadow-sm">
      <h2 className="text-xl font-bold mb-6 text-stone-900">Order Summary</h2>
      
      {errorMessage && (
        <div className="mb-4 p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="space-y-4 text-stone-600 mb-6 text-sm">
        <div className="flex justify-between">
          <span>Subtotal</span>
          <span className="font-semibold text-stone-900">₹{(itemsDiscountAmount > 0 ? originalSubtotal : subtotal).toFixed(0)}</span>
        </div>
        {itemsDiscountAmount > 0 && (
          <div className="flex justify-between text-emerald-700">
            <span>Item Discounts</span>
            <span className="font-semibold">-₹{itemsDiscountAmount.toFixed(0)}</span>
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
        <span>{isProcessing ? "Processing Checkout..." : "Proceed to Checkout"}</span>
        <ChevronRight className="w-5 h-5" />
      </Button>

      <div className="flex items-center justify-center gap-1.5 mt-4 text-xs text-stone-400">
        <ShieldCheck className="w-4 h-4 text-stone-500" />
        <span>Secure transaction backed by Dukaan Guarantee</span>
      </div>
    </div>
  );
}
