import { Sparkles, ArrowRight, ShieldCheck, Truck, RotateCcw, MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store/useStore";

export function Hero() {
  const setIsAgentOpen = useStore((state) => state.setIsAgentOpen);

  const luxuryBrands = [
    "VERSACE",
    "ZARA",
    "GUCCI",
    "PRADA",
    "CALVIN KLEIN",
    "BALENCIAGA",
    "SAINT LAURENT",
    "BURBERRY",
    "RALPH LAURENT",
    "ARMANI",
  ];

  const trustPillars = [
    {
      icon: Truck,
      title: "Express Delivery",
      desc: "Free nationwide shipping over ₹999",
    },
    {
      icon: Sparkles,
      title: "AI Personal Stylist",
      desc: "Instant style advice & live price negotiation",
    },
    {
      icon: ShieldCheck,
      title: "100% Authentic",
      desc: "Directly sourced verified luxury garments",
    },
    {
      icon: RotateCcw,
      title: "Easy 14-Day Returns",
      desc: "Doorstep pickup & instant refunds",
    },
  ];

  return (
    <div className="bg-[#FBF8F3] overflow-hidden">
      {/* Main Hero Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 md:pt-14 pb-12 md:pb-16">
        <div className="grid md:grid-cols-12 gap-10 lg:gap-8 items-center">
          {/* Left: Copy & CTAs */}
          <div className="md:col-span-7 lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-stone-900/5 border border-stone-300/80 text-stone-800 tracking-wider uppercase">
              <span className="w-2 h-2 rounded-full bg-[#C45C26] animate-pulse" />
              <span>Autumn / Winter '26 Collection</span>
            </div>

            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold leading-[1.05] tracking-tight uppercase text-stone-900">
              Find clothes <br className="hidden sm:inline" />
              that <span className="font-serif italic font-normal lowercase tracking-normal text-[#6e1423]">match</span> your style.
            </h1>

            <p className="text-stone-600 text-base sm:text-lg max-w-xl leading-relaxed font-normal">
              Explore our curated designer catalogue crafted for modern elegance.
              Chat directly with our <strong>AI Stylist</strong> to curate your personalized look, check sizing, and negotiate exclusive bundle discounts.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link to="/products">
                <Button className="rounded-full px-8 h-13 text-sm font-semibold bg-stone-900 hover:bg-[#6e1423] text-white shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2 cursor-pointer">
                  <span>Shop Collection</span>
                  <ArrowRight size={16} />
                </Button>
              </Link>
              <button
                onClick={() => setIsAgentOpen(true)}
                type="button"
                className="rounded-full px-6 h-13 text-sm font-semibold bg-white hover:bg-stone-50 text-stone-900 border border-stone-200 shadow-xs hover:shadow-md transition-all duration-300 flex items-center gap-2 cursor-pointer"
              >
                <Sparkles size={16} className="text-[#C45C26]" />
                <span>Chat with Stylist</span>
              </button>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-4 pt-8 border-t border-stone-200/80 max-w-lg">
              <div>
                <p className="font-display text-2xl sm:text-3xl font-extrabold text-stone-900">200+</p>
                <p className="text-xs text-stone-500 font-medium mt-0.5">Top Brands</p>
              </div>
              <div>
                <p className="font-display text-2xl sm:text-3xl font-extrabold text-stone-900">2,500+</p>
                <p className="text-xs text-stone-500 font-medium mt-0.5">Curated Pieces</p>
              </div>
              <div>
                <p className="font-display text-2xl sm:text-3xl font-extrabold text-stone-900">45k+</p>
                <p className="text-xs text-stone-500 font-medium mt-0.5">Happy Clients</p>
              </div>
            </div>
          </div>

          {/* Right: Editorial Image with Floating Tag */}
          <div className="md:col-span-5 lg:col-span-5 relative flex justify-center">
            <div className="relative w-full max-w-md aspect-[4/5] rounded-3xl overflow-hidden shadow-2xl border border-stone-200/80 bg-stone-100">
              <img
                src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=900&auto=format&fit=crop"
                alt="Editorial fashion look"
                className="w-full h-full object-cover object-top hover:scale-105 transition-transform duration-700 ease-out"
                width="900"
                height="1125"
                fetchPriority="high"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-stone-950/60 via-transparent to-transparent pointer-events-none" />

              {/* Floating Feature Pill */}
              <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur-md p-3.5 rounded-2xl border border-stone-200/80 shadow-lg flex items-center justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-bold text-stone-400">Trending Now</p>
                  <p className="text-xs font-semibold text-stone-900">Atelier Tailored Edit</p>
                </div>
                <button
                  onClick={() => setIsAgentOpen(true)}
                  className="bg-stone-900 hover:bg-[#6e1423] text-white text-[11px] font-semibold px-3 py-1.5 rounded-full transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <MessageCircle size={12} />
                  <span>Style me</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Brand Marquee Ticker */}
      <div className="bg-stone-950 py-5 border-y border-stone-800 overflow-hidden">
        <div className="flex whitespace-nowrap animate-marquee">
          {[...luxuryBrands, ...luxuryBrands, ...luxuryBrands].map((b, i) => (
            <div key={i} className="flex items-center mx-6 sm:mx-10 text-stone-300 font-display text-lg sm:text-2xl tracking-widest uppercase opacity-80 hover:opacity-100 transition-opacity">
              <span>{b}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-stone-700 ml-6 sm:ml-10" />
            </div>
          ))}
        </div>
      </div>

      {/* Trust & Assurance Pillars */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {trustPillars.map((p, idx) => {
            const Icon = p.icon;
            return (
              <div
                key={idx}
                className="bg-white p-5 rounded-2xl border border-stone-200/80 shadow-[0_2px_10px_-2px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow flex items-start gap-4"
              >
                <div className="p-2.5 rounded-xl bg-stone-100 text-[#6e1423] flex-shrink-0">
                  <Icon size={20} />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-stone-900">{p.title}</h4>
                  <p className="text-xs text-stone-500 mt-1 leading-relaxed">{p.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
