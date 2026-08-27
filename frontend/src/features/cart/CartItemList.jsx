import { Trash2, Minus, Plus } from "lucide-react";
import { useStore } from "../../store/useStore";

export function CartItemList() {
  const { cart: cartItems, removeFromCart, updateCartQty } = useStore();

  return (
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
  );
}
