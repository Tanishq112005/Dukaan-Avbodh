import { Link } from "react-router-dom";
import { Star } from "lucide-react";
import { cn } from "../../lib/utils";

export function ProductCard({ id, name, price, rating, discount, image_url, size = 'normal' }) {
  const imgUrl = image_url || `https://picsum.photos/seed/${id}/400/400`;
  
  if (size === 'small') {
    return (
      <Link to={`/product/${id}`} className="flex-shrink-0 w-32 border border-slate-100 rounded-lg overflow-hidden block hover:border-indigo-200 transition-colors bg-slate-50 group">
        <div className="relative h-28 bg-white">
          <img src={imgUrl} alt={name} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <div className="p-2">
          <p className="text-xs font-medium text-slate-800 truncate" title={name}>{name}</p>
          <p className="text-[11px] font-bold text-slate-900 mt-0.5">₹{price}</p>
        </div>
      </Link>
    );
  }
  
  return (
    <Link to={`/product/${id}`} className="group cursor-pointer">
      <div className="bg-[#F0EEED] rounded-[20px] aspect-square overflow-hidden mb-4 relative">
        <img src={imgUrl} alt={name} className="w-full h-full object-cover rounded-lg mix-blend-multiply" />
      </div>
      <h3 className="font-bold text-lg mb-1">{name}</h3>
      <div className="flex items-center gap-1 mb-1">
        <div className="flex text-yellow-400">
          {[...Array(5)].map((_, i) => (
            <Star key={i} fill={rating && i < Math.floor(rating) ? "currentColor" : "none"} className="w-4 h-4" />
          ))}
        </div>
        <span className="text-sm text-gray-500">{rating || 0}/5</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-bold text-xl">₹{price}</span>
      </div>
    </Link>
  );
}
