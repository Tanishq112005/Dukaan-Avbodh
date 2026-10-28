import { useEffect } from "react";
import { ChevronRight } from "lucide-react";
import { CartItemList } from "./CartItemList";
import { CartSummary } from "./CartSummary";
import { useStore } from "../../store/useStore";

import { Link } from "react-router-dom";

export function CartPage() {
  const sendAiEvent = useStore(state => state.sendAiEvent);
  const fetchBackendCart = useStore(state => state.fetchBackendCart);

  useEffect(() => {
    // Sync cart with latest database items, negotiated discounts, and pricing
    if (fetchBackendCart) {
      fetchBackendCart();
    }
    // Background event: let the AI agent know user is on the cart/checkout page
    // so it can proactively calculate combinations and pop up a deal!
    sendAiEvent("viewed_checkout");
  }, [sendAiEvent, fetchBackendCart]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8">
      <div className="flex items-center gap-1.5 text-xs sm:text-sm text-stone-400 mb-4 sm:mb-6">
        <Link to="/" className="hover:text-stone-900 cursor-pointer">Home</Link> <ChevronRight className="h-3.5 w-3.5" /> <span className="text-stone-900">Cart</span>
      </div>
      <h1 className="font-display text-2xl sm:text-4xl font-extrabold mb-5 sm:mb-8 uppercase text-stone-900">Your bag</h1>
      
      <div className="flex flex-col lg:flex-row gap-6 sm:gap-8">
        <CartItemList />
        <CartSummary />
      </div>
    </div>
  );
}
