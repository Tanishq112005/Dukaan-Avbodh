import { useEffect, useState } from "react";
import { useStore } from "../../store/useStore";
import { Hero } from "./Hero";
import { ProductSection } from "./ProductSection";
import { BrowseDressStyle } from "./BrowseDressStyle";
import { Sparkles, MessageCircle, ArrowRight, Mail, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

export function HomePage() {
  const { products, fetchProducts, setProducts, setIsAgentOpen } = useStore();
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  useEffect(() => {
    fetchProducts().catch((err) => {
      console.error("Failed to load products for homepage:", err);
      if (products.length === 0) {
        setProducts([
          { id: 1, name: "T-shirt with Tape Details", price: 120, rating: 4.5, discount: 0, type: "t-shirt", brand: "PRADA", description: "Minimalist t-shirt with elegant tape details.", sizes: "S,M,L,XL" },
          { id: 2, name: "Skinny Fit Jeans", price: 240, rating: 3.5, discount: 20, type: "jeans", brand: "Calvin Klein", description: "Comfortable skinny fit jeans.", sizes: "M,L" },
          { id: 3, name: "Checkered Shirt", price: 180, rating: 4.5, discount: 0, type: "shirt", brand: "ZARA", description: "Classic checkered shirt for casual outings.", sizes: "S,M,L" },
          { id: 4, name: "Sleeve Striped T-shirt", price: 130, rating: 4.5, discount: 30, type: "t-shirt", brand: "GUCCI", description: "Trendy striped t-shirt.", sizes: "M,L,XL" },
          { id: 5, name: "Vertical Striped Shirt", price: 212, rating: 5.0, discount: 20, type: "shirt", brand: "RALPH LAUREN", description: "Refined vertical striped button-down shirt.", sizes: "M,L,XL" },
          { id: 6, name: "Courage Graphic T-shirt", price: 145, rating: 4.0, discount: 0, type: "t-shirt", brand: "VERSACE", description: "Signature statement tee.", sizes: "S,M,L" },
          { id: 7, name: "Loose Fit Bermuda Shorts", price: 80, rating: 3.0, discount: 0, type: "short", brand: "CALVIN KLEIN", description: "Relaxed comfort shorts.", sizes: "S,M,L" },
          { id: 8, name: "Faded Skinny Jeans", price: 210, rating: 4.5, discount: 0, type: "jeans", brand: "PRADA", description: "Premium wash tailored denim.", sizes: "30,32,34" },
        ]);
      }
    });
  }, [fetchProducts, products.length, setProducts]);

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (newsletterEmail.trim()) {
      setSubscribed(true);
      setNewsletterEmail("");
      setTimeout(() => setSubscribed(false), 4000);
    }
  };

  return (
    <div className="space-y-0">
      <Hero />

      {/* Featured Collection */}
      <ProductSection title="NEW ARRIVALS" products={products} />

      {/* Interactive AI Stylist Highlight Banner */}
      <section className="py-14 bg-stone-900 text-white relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-8 space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-bold bg-[#C45C26]/20 text-[#C45C26] border border-[#C45C26]/40 uppercase tracking-widest">
                <Sparkles size={12} className="animate-spin text-[#C45C26]" />
                <span>Powered by Dukaan Agentic AI</span>
              </div>
              <h2 className="font-display text-2xl sm:text-3xl lg:text-4xl font-extrabold uppercase tracking-tight">
                Shop with your Personal AI Stylist
              </h2>
              <p className="text-stone-300 text-sm sm:text-base max-w-xl leading-relaxed">
                Looking for a look for dinner, a custom outfit pairing, or a better price?
                Chat with our real-time AI Stylist to get smart recommendations and bargain live for VIP discounts.
              </p>
            </div>
            <div className="md:col-span-4 flex flex-col sm:flex-row md:flex-col gap-3 justify-end">
              <button
                onClick={() => setIsAgentOpen(true)}
                className="px-6 py-3.5 rounded-full bg-[#C45C26] hover:bg-[#a64819] text-white text-xs font-bold tracking-widest uppercase transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer hover:scale-105"
              >
                <MessageCircle size={15} />
                <span>Open AI Stylist Chat</span>
              </button>
              <Link
                to="/products"
                className="px-6 py-3.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-semibold tracking-wider uppercase transition-all border border-white/20 flex items-center justify-center gap-2"
              >
                <span>Browse Catalogue</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Occasion / Lookbook */}
      <BrowseDressStyle />

      {/* VIP Newsletter Section */}
      <section className="py-16 bg-white border-t border-stone-200/80">
        <div className="max-w-4xl mx-auto px-4 text-center space-y-4">
          <span className="text-xs font-bold tracking-widest text-stone-400 uppercase">Atelier Club</span>
          <h2 className="font-display text-2xl sm:text-3xl font-extrabold uppercase text-stone-900 tracking-tight">
            Stay ahead of the new season drops
          </h2>
          <p className="text-stone-500 text-sm max-w-md mx-auto">
            Subscribe to receive private preview links, runway edits, and member-exclusive discount combinations.
          </p>

          <form onSubmit={handleSubscribe} className="max-w-md mx-auto flex items-center gap-2 pt-2">
            <div className="relative flex-1">
              <Mail size={16} className="absolute left-3.5 top-3.5 text-stone-400" />
              <input
                type="email"
                required
                value={newsletterEmail}
                onChange={(e) => setNewsletterEmail(e.target.value)}
                placeholder="Enter your email address"
                className="w-full bg-stone-50 border border-stone-200 rounded-full pl-10 pr-4 py-3 text-xs sm:text-sm outline-none focus:ring-2 focus:ring-stone-900 focus:border-stone-900 transition-all"
              />
            </div>
            <button
              type="submit"
              className="bg-stone-900 hover:bg-[#6e1423] text-white px-6 py-3 rounded-full text-xs font-bold tracking-wider uppercase transition-colors flex-shrink-0 cursor-pointer shadow-xs"
            >
              Subscribe
            </button>
          </form>

          {subscribed && (
            <p className="text-xs text-emerald-700 flex items-center justify-center gap-1.5 font-medium animate-fade-in pt-1">
              <CheckCircle size={14} />
              <span>Thank you! You have been added to the VIP guest list.</span>
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
