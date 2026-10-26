import { Sparkles, Bot, ArrowRight, ShieldCheck, Tag } from "lucide-react";

export function AuthShowcase() {
  const stream1 = [
    {
      id: "a1",
      name: "Velvet Peak-Lapel Blazer",
      brand: "PRADA",
      price: "₹4,200",
      type: "blazer",
      image: "https://picsum.photos/seed/dukaan-blazer/400/400",
    },
    {
      id: "a2",
      name: "Silk Camp-Collar Shirt",
      brand: "CASABLANCA",
      price: "₹1,850",
      type: "shirt",
      image: "https://picsum.photos/seed/dukaan-shirt/400/400",
    },
    {
      id: "a3",
      name: "Selvedge Raw Denim",
      brand: "ACNE STUDIOS",
      price: "₹2,900",
      type: "jeans",
      image: "https://picsum.photos/seed/dukaan-denim/400/400",
    },
    {
      id: "a4",
      name: "Minimalist Cotton Tee",
      brand: "JACQUEMUS",
      price: "₹1,120",
      type: "t-shirt",
      image: "https://picsum.photos/seed/dukaan-tee/400/400",
    },
    {
      id: "a5",
      name: "Wool Pleated Trousers",
      brand: "ISSEY MIYAKE",
      price: "₹2,450",
      type: "trousers",
      image: "https://picsum.photos/seed/dukaan-trousers/400/400",
    },
  ];

  const stream2 = [
    {
      id: "b1",
      name: "Cashmere Knit Sweater",
      brand: "LORO PIANA",
      price: "₹3,400",
      type: "knitwear",
      image: "https://picsum.photos/seed/dukaan-sweater/400/400",
    },
    {
      id: "b2",
      name: "Oversized Wool Trench",
      brand: "BURBERRY",
      price: "₹5,600",
      type: "outerwear",
      image: "https://picsum.photos/seed/dukaan-trench/400/400",
    },
    {
      id: "b3",
      name: "Woven Leather Tote",
      brand: "BOTTEGA VENETA",
      price: "₹6,800",
      type: "accessories",
      image: "https://picsum.photos/seed/dukaan-bag/400/400",
    },
    {
      id: "b4",
      name: "Graphic Poplin Shirt",
      brand: "VERSACE",
      price: "₹2,100",
      type: "shirt",
      image: "https://picsum.photos/seed/dukaan-poplin/400/400",
    },
    {
      id: "b5",
      name: "Tailored Bermuda Shorts",
      brand: "CALVIN KLEIN",
      price: "₹1,400",
      type: "shorts",
      image: "https://picsum.photos/seed/dukaan-shorts/400/400",
    },
  ];

  return (
    <div className="relative w-full h-full min-h-[580px] lg:min-h-[660px] rounded-3xl lg:rounded-[36px] bg-gradient-to-br from-stone-900 via-stone-950 to-[#1e130c] border border-stone-800/80 overflow-hidden shadow-2xl flex flex-col justify-between p-6 sm:p-8">
      {/* Background Running Clothes Streams (Side by Side) */}
      <div className="absolute inset-0 grid grid-cols-2 gap-3 sm:gap-4 p-4 opacity-55 pointer-events-none overflow-hidden">
        {/* Column 1: Upward Marquee */}
        <div className="flex flex-col gap-3 sm:gap-4 animate-marquee-vertical">
          {[...stream1, ...stream1, ...stream1].map((item, idx) => (
            <div
              key={`${item.id}-${idx}`}
              className="bg-stone-900/85 backdrop-blur-md border border-stone-700/60 rounded-2xl p-2.5 shadow-md flex flex-col"
            >
              <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-stone-800 mb-2">
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
                <span className="absolute top-1.5 left-1.5 bg-black/60 backdrop-blur-xs text-white text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                  {item.brand}
                </span>
              </div>
              <p className="text-xs font-semibold text-stone-200 truncate">{item.name}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs font-bold text-amber-300">{item.price}</span>
                <span className="text-[9px] font-semibold text-emerald-400 flex items-center gap-0.5">
                  <Tag size={9} />
                  <span>VIP Live</span>
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Column 2: Reverse Marquee */}
        <div className="flex flex-col gap-3 sm:gap-4 animate-marquee-vertical-reverse pt-8">
          {[...stream2, ...stream2, ...stream2].map((item, idx) => (
            <div
              key={`${item.id}-${idx}`}
              className="bg-stone-900/85 backdrop-blur-md border border-stone-700/60 rounded-2xl p-2.5 shadow-md flex flex-col"
            >
              <div className="relative aspect-square w-full rounded-xl overflow-hidden bg-stone-800 mb-2">
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
                <span className="absolute top-1.5 left-1.5 bg-black/60 backdrop-blur-xs text-white text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                  {item.brand}
                </span>
              </div>
              <p className="text-xs font-semibold text-stone-200 truncate">{item.name}</p>
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs font-bold text-amber-300">{item.price}</span>
                <span className="text-[9px] font-semibold text-emerald-400 flex items-center gap-0.5">
                  <Tag size={9} />
                  <span>AI Bargain</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top & Bottom Vignette Overlay to blend running cards seamlessly */}
      <div className="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-950/40 to-stone-950/90 pointer-events-none" />

      {/* Foreground Content: Top Branding Header */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-2 bg-stone-900/90 backdrop-blur-md border border-stone-700/70 px-3.5 py-1.5 rounded-full shadow-lg">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span className="text-[11px] font-bold tracking-widest uppercase text-stone-200">
            Dukaan AI Runway
          </span>
        </div>
        <span className="text-[11px] font-semibold tracking-wider uppercase text-amber-400/90 bg-amber-400/10 px-3 py-1 rounded-full border border-amber-400/20">
          AW '26 Collection
        </span>
      </div>

      {/* Foreground Content: Floating Centerpiece Dukaan AI Agent Card */}
      <div className="relative z-10 my-auto py-6">
        <div className="bg-stone-900/90 backdrop-blur-xl border border-stone-700/80 rounded-2xl p-5 sm:p-6 shadow-2xl relative overflow-hidden group">
          {/* Subtle Ambient Glow */}
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#C45C26]/25 rounded-full blur-2xl pointer-events-none" />

          {/* AI Agent Status Header */}
          <div className="flex items-center justify-between mb-3.5">
            <div className="flex items-center gap-2.5">
              <div className="relative w-8 h-8 rounded-full bg-gradient-to-tr from-[#6e1423] to-[#C45C26] text-white flex items-center justify-center shadow-md">
                <Bot size={17} />
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-stone-900 rounded-full" />
              </div>
              <div>
                <p className="text-xs font-bold text-white tracking-wide">Dukaan Stylist Agent</p>
                <p className="text-[10px] text-stone-400">Autonomous Fashion Engine</p>
              </div>
            </div>

            <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              <span>Active</span>
            </span>
          </div>

          {/* AI Dialogue Bubble */}
          <div className="bg-stone-950/70 border border-stone-800 rounded-xl p-3.5 mb-3.5 text-xs text-stone-200 leading-relaxed">
            <p>
              "Looking for tailored dinner outfits or want me to negotiate a combo deal? I curate runway looks to your preference and bargain live with merchants on price."
            </p>
          </div>

          {/* Interactive Feature Pills */}
          <div className="grid grid-cols-2 gap-2 text-[11px] font-medium text-stone-300">
            <div className="flex items-center gap-1.5 bg-stone-800/60 border border-stone-700/50 px-2.5 py-1.5 rounded-lg">
              <span className="text-amber-400">✦</span>
              <span>Lookbook Styling</span>
            </div>
            <div className="flex items-center gap-1.5 bg-stone-800/60 border border-stone-700/50 px-2.5 py-1.5 rounded-lg">
              <span className="text-[#C45C26]">✦</span>
              <span>Live Bargaining</span>
            </div>
          </div>
        </div>
      </div>

      {/* Foreground Content: Bottom Guarantee Footer */}
      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-stone-800/80 text-[11px] text-stone-400">
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-emerald-400" />
          <span>100% Certified Authentic Luxury</span>
        </div>
        <div className="flex items-center gap-1 text-stone-300 font-semibold">
          <span>Explore collections</span>
          <ArrowRight size={13} className="text-amber-400" />
        </div>
      </div>
    </div>
  );
}
