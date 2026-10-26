import { ShieldCheck, Sparkles } from "lucide-react";

export function ProductGallery({ product }) {
  const { id, image_url, name } = product;
  const primaryImg = image_url || `https://picsum.photos/seed/${id || 1}/800/1000`;

  return (
    <div className="md:w-1/2">
      {/* Main Single Product Image Container */}
      <div className="relative aspect-[3/4] sm:aspect-[4/5] bg-stone-100 rounded-3xl overflow-hidden border border-stone-200/90 shadow-md group">
        <img
          src={primaryImg}
          alt={name || "Product view"}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
          loading="eager"
        />

        <div className="absolute top-4 left-4 flex flex-col gap-1.5 pointer-events-none">
          <span className="inline-flex items-center gap-1 bg-white/90 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-semibold text-stone-800 border border-stone-200/60 shadow-xs">
            <Sparkles size={11} className="text-[#C45C26]" />
            <span>Atelier Edit</span>
          </span>
          <span className="inline-flex items-center gap-1 bg-white/90 backdrop-blur-md px-3 py-1 rounded-full text-[11px] font-semibold text-emerald-800 border border-emerald-200/60 shadow-xs">
            <ShieldCheck size={11} />
            <span>Verified Authentic</span>
          </span>
        </div>
      </div>
    </div>
  );
}
