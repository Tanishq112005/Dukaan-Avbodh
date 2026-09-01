import { Star } from "lucide-react";
import { useState } from "react";
import { Button } from "../../components/ui/button";
import { Minus, Plus } from "lucide-react";

export function ProductInfo({ product, addToCart }) {
  const [qty, setQty] = useState(1);
  const [selSize, setSelSize] = useState('Large');
  const [selColor, setSelColor] = useState('Dark');

  const productSizes = product.sizes ? product.sizes.split(',') : ['Small', 'Medium', 'Large', 'X-Large'];

  return (
    <div className="md:w-1/2 py-4">
      {product.brand && <p className="text-gray-500 font-bold uppercase tracking-widest mb-1">{product.brand}</p>}
      <h1 className="text-4xl font-black mb-2 uppercase">{product.name}</h1>
      <div className="flex items-center gap-2 mb-4">
        <div className="flex text-yellow-400"><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star className="w-5 h-5" /></div>
        <span className="text-sm">{product.rating || 4.5}/5</span>
      </div>
      <div className="flex items-center gap-3 mb-6">
        <span className="font-bold text-3xl">₹{product.price}</span>
      </div>
      <p className="text-gray-500 mb-6">{product.description}</p>
      <hr className="my-6" />
      <div className="mb-6">
        <p className="text-gray-500 mb-3">Choose Size</p>
        <div className="flex flex-wrap gap-3">
          {productSizes.map(size => (
            <button key={size} onClick={() => setSelSize(size)} className={`px-6 py-3 rounded-full ${selSize === size ? 'bg-black text-white' : 'bg-[#F0F0F0] text-gray-500'}`}>{size}</button>
          ))}
        </div>
      </div>
      <hr className="my-6" />
      <div className="flex gap-4">
        <div className="flex items-center justify-between bg-[#F0F0F0] rounded-full px-6 py-4 w-40">
          <Minus className="cursor-pointer" onClick={() => setQty(Math.max(1, qty - 1))} />
          <span className="font-bold">{qty}</span>
          <Plus className="cursor-pointer" onClick={() => setQty(qty + 1)} />
        </div>
        <Button className="flex-1 rounded-full py-6 text-lg" onClick={() => addToCart(qty, selSize, selColor)}>Add to Cart</Button>
      </div>
    </div>
  );
}
