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

  const handleCheckout = async () => {
    if (!token) return alert("Please login first by clicking the User icon in top right!");
    
    try {
      for (const item of cartItems) {
        await axios.post("http://localhost:8000/checkout/", {
          product_id: item.id,
          requested_discount: 20.0
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      alert("Checkout successful via FastAPI!");
      clearCart();
    } catch (err) {
      console.error(err);
      alert("Checkout failed. See console.");
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
