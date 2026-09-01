import { Link } from "react-router-dom";
import { Star } from "lucide-react";

export function ProductCard({ id, name, price, rating, discount, image_url }) {
  const imgUrl = image_url || `https://picsum.photos/seed/${id}/400/400`;
  
  return (
    <Link to={`/product/${id}`} className="group cursor-pointer">
      <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden mb-4 relative">
        <img src={imgUrl} alt={name} className="w-full h-full object-cover rounded-lg mix-blend-multiply" />
      </div>
      <h3 className="font-bold text-lg mb-1">{name}</h3>
      <div className="flex items-center gap-1 mb-1">
        <div className="flex text-yellow-400">
          {[...Array(5)].map((_, i) => (
            <Star key={i} fill={i < Math.floor(rating) ? "currentColor" : "none"} className="w-4 h-4" />
          ))}
        </div>
        <span className="text-sm text-gray-500">{rating}/5</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-bold text-xl">₹{price}</span>
      </div>
    </Link>
  );
}
