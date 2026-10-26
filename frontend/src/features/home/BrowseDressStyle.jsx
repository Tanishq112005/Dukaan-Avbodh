import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

const occasions = [
  {
    name: "Casual Wear",
    subtitle: "Everyday effortless comfort",
    img: "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?q=80&w=800&auto=format&fit=crop",
    type: "t-shirt",
  },
  {
    name: "Formal & Business",
    subtitle: "Clean cuts & executive tailoring",
    img: "https://images.unsplash.com/photo-1594938291221-94f18cbb5660?q=80&w=800&auto=format&fit=crop",
    type: "shirt",
  },
  {
    name: "Evening & Party",
    subtitle: "Bold silhouettes for night outs",
    img: "https://images.unsplash.com/photo-1566288623394-377af472d81b?q=80&w=800&auto=format&fit=crop",
    type: "jeans",
  },
  {
    name: "Athleisure & Gym",
    subtitle: "High-performance flex apparel",
    img: "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=800&auto=format&fit=crop",
    type: "hoodie",
  },
];

export function BrowseDressStyle() {
  return (
    <section className="py-16 md:py-24 bg-[#FBF8F3] border-t border-stone-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <p className="text-xs font-bold tracking-widest text-[#C45C26] uppercase mb-2">Lookbook</p>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold uppercase text-stone-900 tracking-tight">
            Shop by Occasion
          </h2>
          <p className="text-stone-500 text-sm mt-3">
            Whether dressing for the boardroom, weekend lounging, or a rooftop soirée, find garments tailored to the moment.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {occasions.map((o) => (
            <Link
              key={o.name}
              to="/products"
              className="group relative block rounded-3xl overflow-hidden aspect-[3/4] bg-stone-900 shadow-md hover:shadow-xl transition-all duration-500"
            >
              <img
                src={o.img}
                alt={o.name}
                loading="lazy"
                decoding="async"
                width="600"
                height="800"
                className="w-full h-full object-cover group-hover:scale-108 transition-transform duration-700 ease-out opacity-90 group-hover:opacity-100"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-stone-950/80 via-stone-950/20 to-transparent transition-opacity group-hover:from-stone-950/90" />

              <div className="absolute inset-x-5 bottom-5 flex items-end justify-between">
                <div>
                  <h3 className="font-display text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
                    {o.name}
                  </h3>
                  <p className="text-xs text-stone-300 mt-1 font-medium">{o.subtitle}</p>
                </div>
                <div className="w-9 h-9 rounded-full bg-white/20 backdrop-blur-md text-white flex items-center justify-center group-hover:bg-white group-hover:text-stone-900 transition-all duration-300 flex-shrink-0 ml-2">
                  <ArrowUpRight size={18} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
