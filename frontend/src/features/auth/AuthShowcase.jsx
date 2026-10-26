import { useState, useEffect } from "react";
import { Sparkles, ChevronLeft, ChevronRight, Bot, ShieldCheck } from "lucide-react";

export function AuthShowcase() {
  const slides = [
    {
      image: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1000&auto=format&fit=crop&q=80",
      tag: "Autumn / Winter '26 Edit",
      title: "Tailored Peak-Lapel Outerwear",
      stylistNote: "Curated by Dukaan AI Stylist for effortless evening elegance.",
      aiBadge: "Lookbook Curation",
    },
    {
      image: "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=1000&auto=format&fit=crop&q=80",
      tag: "Runway Capsule",
      title: "Cashmere Trench & Tonal Layers",
      stylistNote: "Negotiated live with merchant at member-exclusive VIP discount.",
      aiBadge: "Price Bargaining",
    },
    {
      image: "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=1000&auto=format&fit=crop&q=80",
      tag: "Atelier Minimal",
      title: "Silk Poplin Shirt & Raw Denim",
      stylistNote: "Instant outfit pairings curated dynamically for your wardrobe.",
      aiBadge: "Smart Combo",
    },
    {
      image: "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1000&auto=format&fit=crop&q=80",
      tag: "Agentic Fashion",
      title: "Dukaan Autonomous AI Stylist",
      stylistNote: "Chat live with our AI agent to source, size, and bargain on prices.",
      aiBadge: "Live AI Agent",
    },
    {
      image: "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=1000&auto=format&fit=crop&q=80",
      tag: "Couture Selection",
      title: "Draped Silk & Sculpted Silhouettes",
      stylistNote: "Handcrafted designer apparel delivered directly to your doorstep.",
      aiBadge: "Express Delivery",
    },
  ];

  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent((prev) => (prev + 1) % slides.length);
    }, 3800);
    return () => clearInterval(timer);
  }, [slides.length]);

  const prevSlide = () => {
    setCurrent((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const nextSlide = () => {
    setCurrent((prev) => (prev + 1) % slides.length);
  };

  return (
    <div className="relative w-full h-full min-h-[580px] lg:min-h-[660px] rounded-3xl lg:rounded-[36px] overflow-hidden shadow-2xl bg-stone-950 border border-stone-800/80 group flex flex-col justify-between">
      {/* Sliding Images Track - Smooth Horizontal Slide */}
      <div
        className="flex w-full h-full absolute inset-0 transition-transform duration-700 ease-in-out"
        style={{ transform: `translateX(-${current * 100}%)` }}
      >
        {slides.map((slide, idx) => (
          <div key={idx} className="relative w-full h-full flex-shrink-0">
            <img
              src={slide.image}
              alt={slide.title}
              className="w-full h-full object-cover"
              loading={idx === 0 ? "eager" : "lazy"}
            />
          </div>
        ))}
      </div>

      {/* Cinematic Gradient Overlays to Ensure Crystal-Clear Contrast */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/25 to-black/50 pointer-events-none" />

      {/* Top Floating Badges */}
      <div className="relative z-10 p-6 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md border border-white/20 px-3.5 py-1.5 rounded-full shadow-lg">
          <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
          <span className="text-[11px] font-bold tracking-widest uppercase text-white">
            Dukaan Runway
          </span>
        </div>

        <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-md border border-white/20 text-amber-300 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
          <Bot size={13} className="text-amber-400" />
          <span>{slides[current].aiBadge}</span>
        </div>
      </div>

      {/* Manual Slide Navigation Controls */}
      <button
        type="button"
        onClick={prevSlide}
        className="absolute left-4 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-black/40 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all cursor-pointer shadow-md"
        aria-label="Previous slide"
      >
        <ChevronLeft size={18} />
      </button>

      <button
        type="button"
        onClick={nextSlide}
        className="absolute right-4 top-1/2 -translate-y-1/2 z-20 w-9 h-9 rounded-full bg-black/40 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all cursor-pointer shadow-md"
        aria-label="Next slide"
      >
        <ChevronRight size={18} />
      </button>

      {/* Bottom Editorial Content & Progress */}
      <div className="relative z-10 p-6 sm:p-8 space-y-3.5">
        <div>
          <p className="text-[10px] sm:text-[11px] font-bold uppercase tracking-[0.2em] text-[#C45C26] mb-1">
            {slides[current].tag}
          </p>
          <h3 className="font-display text-xl sm:text-2xl lg:text-3xl font-extrabold uppercase text-white tracking-tight leading-snug">
            {slides[current].title}
          </h3>
          <p className="text-xs sm:text-sm text-stone-300 mt-1 max-w-lg leading-relaxed">
            {slides[current].stylistNote}
          </p>
        </div>

        {/* Slide Progress Indicators */}
        <div className="flex items-center justify-between pt-3 border-t border-white/20">
          <div className="flex items-center gap-1.5">
            {slides.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setCurrent(idx)}
                className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                  current === idx ? "w-8 bg-amber-400" : "w-2 bg-white/30 hover:bg-white/60"
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>

          <div className="flex items-center gap-1.5 text-[11px] font-medium text-stone-300">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span>100% Certified Authentic Luxury</span>
          </div>
        </div>
      </div>
    </div>
  );
}
