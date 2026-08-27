import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Star, Minus, Plus, ChevronRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { products, addToCart: addToZustandCart } = useStore();
  const [qty, setQty] = useState(1);
  const [selSize, setSelSize] = useState('Large');
  const [selColor, setSelColor] = useState('Dark');
  
  const product = products.find(p => p.id == id) || {
    id, name: "ONE LIFE GRAPHIC T-SHIRT", price: 260, discount: 40, rating: 4.5, brand: "ZARA",
    description: "This graphic t-shirt which is perfect for any occasion. Crafted from a soft and breathable fabric, it offers superior comfort and style.",
    sizes: "Small,Medium,Large,X-Large"
  };

  const productSizes = product.sizes ? product.sizes.split(',') : ['Small', 'Medium', 'Large', 'X-Large'];

  const addToCart = () => {
    addToZustandCart(product, qty, selSize, selColor);
    navigate("/cart");
  };

  const originalPrice = product.discount ? (product.price / (1 - product.discount / 100)).toFixed(0) : product.price;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <span>Home</span> <ChevronRight className="h-4 w-4" /> <span>Shop</span> <ChevronRight className="h-4 w-4" /> <span className="text-black capitalize">{product.type || "T-shirts"}</span>
      </div>
      <div className="flex flex-col md:flex-row gap-10">
        <div className="md:w-1/2 flex gap-4">
          <div className="flex flex-col gap-4 w-1/4">
             <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={product.image_url || `https://picsum.photos/seed/${id}/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
             <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={product.image_url || `https://picsum.photos/seed/${id}a/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
             <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden"><img src={product.image_url || `https://picsum.photos/seed/${id}b/200/200`} className="w-full h-full object-cover mix-blend-multiply"/></div>
          </div>
          <div className="bg-[#F0EEED] rounded-[20px] w-3/4 aspect-[3/4] overflow-hidden"><img src={product.image_url || `https://picsum.photos/seed/${id}/800/1000`} className="w-full h-full object-cover mix-blend-multiply"/></div>
        </div>
        <div className="md:w-1/2 py-4">
          {product.brand && <p className="text-gray-500 font-bold uppercase tracking-widest mb-1">{product.brand}</p>}
          <h1 className="text-4xl font-black mb-2 uppercase">{product.name}</h1>
          <div className="flex items-center gap-2 mb-4">
            <div className="flex text-yellow-400"><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star fill="currentColor" className="w-5 h-5" /><Star className="w-5 h-5" /></div>
            <span className="text-sm">{product.rating || 4.5}/5</span>
          </div>
          <div className="flex items-center gap-3 mb-6">
            <span className="font-bold text-3xl">₹{product.price}</span>
            {product.discount > 0 && <span className="font-bold text-3xl text-gray-400 line-through">₹{originalPrice}</span>}
            {product.discount > 0 && <span className="bg-red-100 text-red-500 font-bold px-3 py-1 rounded-full">-{product.discount}%</span>}
          </div>
          <p className="text-gray-500 mb-6">{product.description}</p>
          <hr className="my-6" />
          <div className="mb-6">
            <p className="text-gray-500 mb-3">Select Colors</p>
            <div className="flex gap-3">
              <div onClick={() => setSelColor('Dark')} className={`w-9 h-9 rounded-full bg-[#314F4A] cursor-pointer ${selColor === 'Dark' ? 'ring-2 ring-offset-2 ring-black' : ''}`}></div>
              <div onClick={() => setSelColor('Navy')} className={`w-9 h-9 rounded-full bg-[#31344F] cursor-pointer ${selColor === 'Navy' ? 'ring-2 ring-offset-2 ring-black' : ''}`}></div>
            </div>
          </div>
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
            <div className="flex items-center justify-between bg-[#F0F0F0] rounded-full px-5 py-3 w-32">
              <Minus className="w-5 h-5 cursor-pointer" onClick={() => setQty(Math.max(1, qty-1))} />
              <span className="font-bold">{qty}</span>
              <Plus className="w-5 h-5 cursor-pointer" onClick={() => setQty(qty+1)} />
            </div>
            <Button className="flex-1 rounded-full text-lg py-6" onClick={addToCart}>Add to Cart</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
