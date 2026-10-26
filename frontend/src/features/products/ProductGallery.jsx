import { useState } from "react";
import { ShieldCheck, Sparkles } from "lucide-react";

export function ProductGallery({ product }) {
  const { id, image_url, name } = product;
  const primaryImg = image_url || `https://picsum.photos/seed/${id || 1}/800/1000`;

  // Generate 3 alternate gallery angles for an authentic luxury ecommerce gallery
  const galleryImages = [
    primaryImg,
    `https://picsum.photos/seed/${(Number(id) || 1) + 101}/800/1000`,
    `https://picsum.photos/seed/${(Number(id) || 1) + 202}/800/1000`,
  ];

  const [selectedImg, setSelectedImg] = useState(galleryImages[0]);

  return (
    <div className="md:w-1/2 flex flex-col-reverse lg:flex-row gap-4">
      {/* Thumbnail Strips */}
      <div className="flex lg:flex-col gap-3 justify-center lg:justify-start">
        {galleryImages.map((img, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setSelectedImg(img)}
            className={`w-18 h-22 sm:w-20 sm:h-26 rounded-2xl overflow-hidden border-2 transition-all cursor-pointer bg-stone-100 ${
              selectedImg === img
                ? "border-stone-900 shadow-sm"
                : "border-transparent opacity-70 hover:opacity-100 hover:border-stone-300"
            }`}
          >
            <img
              src={img}
              alt={`${name || "Product"} view ${idx + 1}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          </button>
        ))}
      </div>

      {/* Main Feature Image Container */}
      <div className="flex-1 relative aspect-[3/4] bg-stone-100 rounded-3xl overflow-hidden border border-stone-200/90 shadow-md group">
        <img
          src={selectedImg}
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
