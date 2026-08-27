import { ChevronRight, Trash2, Minus, Plus } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useStore } from "../../store/useStore";
import axios from "axios";

export function CartPage() {
  const { cart: cartItems, removeFromCart, updateCartQty, token, clearCart } = useStore();

  const subtotal = cartItems.reduce((acc, item) => acc + item.price * item.qty, 0);
  const discount = subtotal * 0.2; // 20%
  const delivery = 15;
  const total = subtotal - discount + delivery;

  const handleCheckout = async () => {
    if (!token) return alert("Please login first by clicking the User icon in top right!");
    
    try {
      // Backend only takes one item per checkout right now. We'll do them sequentially.
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <span>Home</span> <ChevronRight className="h-4 w-4" /> <span className="text-black">Cart</span>
      </div>
      <h1 className="text-4xl font-black mb-8 uppercase">Your Cart</h1>
      
      <div className="flex flex-col md:flex-row gap-8">
        <div className="md:w-2/3 border border-gray-200 rounded-[20px] p-4 md:p-6 space-y-6">
          {cartItems.map(item => (
            <div key={item.id} className="flex gap-4">
              <div className="w-24 h-24 bg-[#F0F0F0] rounded-xl overflow-hidden flex-shrink-0">
                <img src={item.image_url || `https://picsum.photos/seed/${item.id}/200/200`} alt={item.name} className="w-full h-full object-cover mix-blend-multiply" />
              </div>
              <div className="flex-1 flex flex-col justify-between">
                <div className="flex justify-between">
                  <h3 className="font-bold text-lg">{item.name}</h3>
                  <Trash2 className="w-5 h-5 text-red-500 cursor-pointer" onClick={() => removeFromCart(item.id, item.size, item.color)} />
                </div>
                <p className="text-sm text-gray-500">Size: {item.size}</p>
                <p className="text-sm text-gray-500">Color: {item.color}</p>
                <div className="flex justify-between items-center mt-2">
                  <span className="font-bold text-xl">₹{item.price}</span>
                  <div className="flex items-center justify-between bg-[#F0F0F0] rounded-full px-4 py-2 w-28">
                    <Minus className="w-4 h-4 cursor-pointer" onClick={() => updateCartQty(item.id, item.size, item.color, item.qty - 1)} />
                    <span className="font-bold text-sm">{item.qty}</span>
                    <Plus className="w-4 h-4 cursor-pointer" onClick={() => updateCartQty(item.id, item.size, item.color, item.qty + 1)} />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

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
      </div>
    </div>
  );
}
