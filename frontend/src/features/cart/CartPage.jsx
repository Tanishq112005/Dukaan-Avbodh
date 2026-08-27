import { ChevronRight } from "lucide-react";
import { CartItemList } from "./CartItemList";
import { CartSummary } from "./CartSummary";

export function CartPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <span>Home</span> <ChevronRight className="h-4 w-4" /> <span className="text-black">Cart</span>
      </div>
      <h1 className="text-4xl font-black mb-8 uppercase">Your Cart</h1>
      
      <div className="flex flex-col md:flex-row gap-8">
        <CartItemList />
        <CartSummary />
      </div>
    </div>
  );
}
