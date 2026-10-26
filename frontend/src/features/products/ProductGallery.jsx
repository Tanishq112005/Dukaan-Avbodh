import { ShieldCheck, Sparkles } from "lucide-react";

export function ProductGallery({ product }) {
  const { id, image_url, name } = product;
  const primaryImg = image_url || `https://picsum.photos/seed/${id || 1}/800/1000`;

  return (
    <div className="w-full">
      {/* Main Single Product Image Container with refined height & proportions */}
      <div className="relative aspect-[3/4] max-h-[460px] sm:max-h-[500px] w-full bg-stone-100 rounded-2xl overflow-hidden border border-stone-200/90 shadow-xs group">
        <img
          src={primaryImg}
          alt={name || "Product view"}
          className="w-full h-full object-cover object-top group-hover:scale-102 transition-transform duration-500 ease-out"
          loading="eager"
        />

        {/* Floating Atelier Badges */}
        <div className="absolute top-3 left-3 flex flex-col gap-1 pointer-events-none">
          <span className="inline-flex items-center gap-1 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-stone-800 border border-stone-200/80 shadow-xs">
            <Sparkles size={10} className="text-[#C45C26]" />
            <span>Atelier Edit</span>
          </span>
          <span className="inline-flex items-center gap-1 bg-white/95 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[10px] font-semibold text-emerald-800 border border-emerald-200/80 shadow-xs">
            <ShieldCheck size={10} />
            <span>Verified Authentic</span>
          </span>
        </div>
      </div>
    </div>
  );
}
