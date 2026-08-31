import { ChevronRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store/useStore";
import axios from "axios";

export function CartSummary() {
  const { cart: cartItems, token, clearCart } = useStore();

  const subtotal = cartItems.reduce((acc, item) => acc + item.price * item.qty, 0);
  const discount = subtotal * 0.2; // 20%
  const delivery = 15;
  const total = subtotal - discount + delivery;

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
    if (!token) return alert("Please login first by clicking the User icon in top right!");
    
    const res = await loadRazorpayScript();
    if (!res) {
      alert("Razorpay SDK failed to load. Are you online?");
      return;
    }

    try {
      // 1. Create Order on Backend
      const amountPaise = Math.round(total * 100);
      const orderResponse = await axios.post("http://localhost:8000/api/payment/create-order", {
        amount: amountPaise,
        currency: "INR",
        receipt: `receipt_cart_${Date.now()}`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const order = orderResponse.data;

      // 2. Open Razorpay Modal
      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID || "rzp_test_TWV2ichCwzRcvo", // Use env var in production
        amount: order.amount,
        currency: order.currency,
        name: "Dukaan Shopping",
        description: "Test Transaction",
        order_id: order.id,
        handler: async function (response) {
          // 3. Verify Payment on Backend
          try {
            const verifyRes = await axios.post("http://localhost:8000/api/payment/verify", {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            }, {
              headers: { Authorization: `Bearer ${token}` }
            });

            if (verifyRes.data.success) {
              alert("Payment Successful & Verified!");
              
              // Also call the old internal checkout to clear stock/log purchase if needed
              for (const item of cartItems) {
                await axios.post("http://localhost:8000/checkout/", {
                  product_id: item.id,
                  requested_discount: 20.0
                }, {
                  headers: { Authorization: `Bearer ${token}` }
                });
              }
              
              clearCart();
            }
          } catch (err) {
            console.error(err);
            alert("Payment verification failed on server.");
          }
        },
        prefill: {
          name: "Test User",
          email: "test@example.com",
          contact: "9999999999"
        },
        theme: {
          color: "#000000"
        }
      };

      const rzp1 = new window.Razorpay(options);
      rzp1.on('payment.failed', function (response){
        alert("Payment failed: " + response.error.description);
      });
      rzp1.open();

    } catch (err) {
      console.error(err);
      alert("Failed to initialize checkout. See console.");
    }
  };

  return (
    <div className="md:w-1/3 border border-gray-200 rounded-[20px] p-6 h-fit">
      <h2 className="text-xl font-bold mb-6">Order Summary</h2>
      <div className="space-y-4 text-gray-500 mb-6">
        <div className="flex justify-between"><span>Subtotal</span><span className="font-bold text-black">₹{subtotal}</span></div>
        <div className="flex justify-between"><span>Discount (-20%)</span><span className="font-bold text-red-500">-₹{discount.toFixed(0)}</span></div>
        <div className="flex justify-between"><span>Delivery Fee</span><span className="font-bold text-black">₹{delivery}</span></div>
      </div>
      <hr className="my-4" />
      <div className="flex justify-between text-xl font-bold mb-6">
        <span>Total</span><span>₹{total.toFixed(0)}</span>
      </div>
      <div className="flex gap-2 mb-6">
        <Input placeholder="Add promo code" className="bg-[#F0F0F0] border-none rounded-full" />
        <Button className="rounded-full px-6">Apply</Button>
      </div>
      <Button className="w-full rounded-full py-6 text-lg" onClick={handleCheckout}>
        Go to Checkout <ChevronRight className="ml-2 w-5 h-5" />
      </Button>
    </div>
  );
}
