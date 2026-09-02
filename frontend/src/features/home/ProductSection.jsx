import { ProductCard } from "../../components/ui/ProductCard";
import { Link } from "react-router-dom";

export function ProductSection({ title, products, eager = false }) {
  return (
    <section className="py-16 md:py-20 border-t border-hairline">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-10">
          <h2 className="font-display text-3xl md:text-5xl">{title}</h2>
          <Link to="/products" className="text-sm text-ink/60 hover:text-ink border-b border-hairline hover:border-ink pb-0.5">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-5 gap-y-10 md:gap-x-8">
          {products.slice(0, 4).map((p, i) => (
            <ProductCard key={p.id} {...p} index={i} eager={eager && i < 2} />
          ))}
        </div>
      </div>
    </section>
  );
}
