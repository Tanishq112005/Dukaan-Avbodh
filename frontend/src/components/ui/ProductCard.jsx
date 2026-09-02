import { Link } from "react-router-dom";
import { Star } from "lucide-react";
import { cn } from "../../lib/utils";

export function ProductCard({ id, name, price, rating, discount, image_url, size = 'normal' }) {
  const imgUrl = image_url || `https://picsum.photos/seed/${id}/400/400`;
  
  if (size === 'small') {
    return (
      <Link to={`/product/${id}`} className="flex-shrink-0 w-32 border border-stone-100 rounded-xl overflow-hidden block hover:border-[#C45C26]/40 transition-colors bg-white group">
        <div className="relative h-28 bg-[#F3EEE6] overflow-hidden">
          <img src={imgUrl} alt={name} className="product-card-img w-full h-full object-cover" />
        </div>
        <div className="p-2">
          <p className="text-xs font-medium text-stone-800 truncate" title={name}>{name}</p>
          <p className="text-[11px] font-bold text-stone-900 mt-0.5">₹{price}</p>
        </div>
      </Link>
    );
  }
  
  return (
    <Link to={`/product/${id}`} className="group cursor-pointer block">
      <div className="bg-[#EFE8DE] rounded-[24px] aspect-[4/5] overflow-hidden mb-4 relative">
        <img src={imgUrl} alt={name} className="product-card-img w-full h-full object-cover" />
        <div className="absolute inset-x-3 bottom-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="inline-block bg-white/95 text-[11px] font-bold tracking-widest uppercase px-3 py-1.5 rounded-full">
            View
          </span>
        </div>
      </div>
      <h3 className="font-semibold text-base mb-1 leading-snug">{name}</h3>
      <div className="flex items-center gap-1 mb-1">
        <div className="flex text-[#C45C26]">
          {[...Array(5)].map((_, i) => (
            <Star key={i} fill={rating && i < Math.floor(rating) ? "currentColor" : "none"} className="w-3.5 h-3.5" />
          ))}
        </div>
        <span className="text-xs text-stone-400">{rating || 0}/5</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-bold text-lg">₹{price}</span>
      </div>
    </Link>
  );
}
