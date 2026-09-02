import { Link } from "react-router-dom";
import { Star } from "lucide-react";

export function ProductCard({ id, name, price, rating, discount, image_url, index, eager = false, size = "normal" }) {
  const imgUrl = image_url || `https://picsum.photos/seed/${id}/600/750`;

  if (size === "small") {
    return (
      <Link to={`/product/${id}`} className="flex-shrink-0 w-32 border border-hairline overflow-hidden block hover:border-ink/40 transition-colors bg-paper group">
        <div className="relative h-28 bg-stone-surface overflow-hidden">
          <img
            src={imgUrl}
            alt={name}
            className="product-card-img w-full h-full object-cover"
            loading="lazy"
            decoding="async"
            width="128"
            height="112"
          />
        </div>
        <div className="p-2">
          <p className="text-xs font-medium text-ink truncate" title={name}>{name}</p>
          <p className="text-[11px] font-bold text-ink mt-0.5">₹{price}</p>
        </div>
      </Link>
    );
  }

  return (
    <Link to={`/product/${id}`} className="group cursor-pointer block">
      <div className="img-frame aspect-[4/5] border border-hairline mb-4 relative">
        {typeof index === "number" && (
          <span className="absolute top-3 left-3 z-10 text-[11px] font-medium text-ink/50 bg-paper/90 px-1.5 py-0.5">
            {String(index + 1).padStart(2, "0")}
          </span>
        )}
        <img
          src={imgUrl}
          alt={name}
          className="product-card-img w-full h-full object-cover"
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          width="600"
          height="750"
          onLoad={(e) => e.currentTarget.setAttribute("data-loaded", "true")}
        />
        <div className="absolute inset-x-3 bottom-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="inline-block bg-paper text-[11px] font-semibold px-3 py-1.5 border border-ink/10">
            View
          </span>
        </div>
      </div>
      <h3 className="font-medium text-base mb-1 leading-snug">{name}</h3>
      <div className="flex items-center gap-1 mb-1">
        <div className="flex text-oxblood">
          {[...Array(5)].map((_, i) => (
            <Star key={i} fill={rating && i < Math.floor(rating) ? "currentColor" : "none"} strokeWidth={1.25} className="w-3.5 h-3.5" />
          ))}
        </div>
        <span className="text-xs text-ink/40">{rating || 0}/5</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-semibold text-base">₹{price}</span>
        {discount > 0 && <span className="text-xs text-ink/40 line-through">₹{Math.round(price / (1 - discount / 100))}</span>}
      </div>
    </Link>
  );
}
