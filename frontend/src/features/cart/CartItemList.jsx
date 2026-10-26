import { Trash2, Minus, Plus, ShoppingBag, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useStore } from "../../store/useStore";

export function CartItemList() {
  const { cart: cartItems, removeFromCart, updateCartQty } = useStore();

  if (!cartItems || cartItems.length === 0) {
    return (
      <div className="md:w-2/3 border border-stone-200/80 bg-white rounded-3xl p-10 text-center shadow-xs">
        <div className="w-16 h-16 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-4 text-[#C45C26]">
          <ShoppingBag size={28} />
        </div>
        <h3 className="font-display text-xl font-bold text-stone-900 mb-2">
          Your shopping bag is empty
        </h3>
        <p className="text-stone-500 text-sm max-w-sm mx-auto mb-6">
          Looks like you haven't added any designer garments to your bag yet. Explore our curated collections to start styling.
        </p>
        <Link
          to="/products"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-stone-900 hover:bg-[#6e1423] text-white text-xs font-semibold tracking-wider uppercase transition-colors"
        >
          <span>Explore Collections</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    );
  }

  return (
    <div className="md:w-2/3 border border-stone-200/80 bg-white rounded-3xl p-6 sm:p-8 space-y-6 shadow-xs">
      <div className="flex items-center justify-between pb-4 border-b border-stone-100">
        <h2 className="font-bold text-sm tracking-wider uppercase text-stone-900">
          Items in Bag ({cartItems.reduce((acc, i) => acc + (i.qty || 1), 0)})
        </h2>
      </div>

      <div className="divide-y divide-stone-100 space-y-6">
        {cartItems.map((item, idx) => {
          const finalId = item.id || item.product_id;
          const formattedPrice = `₹${Number(item.price || 0).toLocaleString("en-IN")}`;

          return (
            <div key={`${finalId}-${item.size || "M"}-${idx}`} className="pt-6 first:pt-0 flex gap-4 sm:gap-6">
              {/* Product Thumbnail */}
              <div className="w-22 h-26 sm:w-24 sm:h-28 bg-stone-100 rounded-2xl overflow-hidden flex-shrink-0 border border-stone-200/80">
                <img
                  src={item.image_url || `https://picsum.photos/seed/${finalId}/400/500`}
                  alt={item.name}
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Item Info & Actions */}
              <div className="flex-1 flex flex-col justify-between py-0.5">
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      {item.brand && (
                        <p className="text-[10px] font-bold uppercase tracking-widest text-stone-400">
                          {item.brand}
                        </p>
                      )}
                      <h3 className="font-semibold text-base text-stone-900 leading-snug line-clamp-1">
                        {item.name}
                      </h3>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.id, item.size, item.color)}
                      className="text-stone-400 hover:text-red-600 p-1 rounded-full transition-colors cursor-pointer"
                      title="Remove item"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <div className="flex items-center gap-3 mt-1.5 text-xs text-stone-500">
                    <span>Size: <strong className="text-stone-800">{item.size || "M"}</strong></span>
                    {item.color && (
                      <>
                        <span>·</span>
                        <span>Color: <strong className="text-stone-800">{item.color}</strong></span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between mt-4 pt-2">
                  <span className="font-bold text-lg text-stone-900">{formattedPrice}</span>

                  {/* Quantity Stepper */}
                  <div className="flex items-center justify-between bg-stone-100 rounded-xl px-3 py-1.5 w-26 border border-stone-200/60">
                    <button
                      type="button"
                      onClick={() => updateCartQty(item.id, item.size, item.color, Math.max(1, (item.qty || 1) - 1))}
                      className="text-stone-500 hover:text-stone-900 p-0.5 cursor-pointer"
                      title="Decrease quantity"
                    >
                      <Minus size={13} />
                    </button>
                    <span className="font-bold text-xs text-stone-900">{item.qty || 1}</span>
                    <button
                      type="button"
                      onClick={() => updateCartQty(item.id, item.size, item.color, (item.qty || 1) + 1)}
                      className="text-stone-500 hover:text-stone-900 p-0.5 cursor-pointer"
                      title="Increase quantity"
                    >
                      <Plus size={13} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
