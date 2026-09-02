import { useEffect } from "react";
import { ChevronRight } from "lucide-react";
import { CartItemList } from "./CartItemList";
import { CartSummary } from "./CartSummary";
import { useStore } from "../../store/useStore";

import { Link } from "react-router-dom";

export function CartPage() {
  const sendAiEvent = useStore(state => state.sendAiEvent);

  useEffect(() => {
    // Background event: let the AI agent know user is on the cart/checkout page
    // so it can proactively calculate combinations and pop up a deal!
    sendAiEvent("viewed_checkout");
  }, [sendAiEvent]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-2 text-sm text-stone-400 mb-6">
        <Link to="/" className="hover:text-stone-900 cursor-pointer">Home</Link> <ChevronRight className="h-4 w-4" /> <span className="text-stone-900">Cart</span>
      </div>
      <h1 className="font-display text-4xl font-extrabold mb-8 uppercase">Your bag</h1>
      
      <div className="flex flex-col md:flex-row gap-8">
        <CartItemList />
        <CartSummary />
      </div>
    </div>
  );
}
