import { ProductCard } from "../../components/ui/ProductCard";
import { Button } from "../../components/ui/button";
import { Link } from "react-router-dom";

export function ProductSection({ title, products }) {
  return (
    <section className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-10">
          <div>
            <p className="text-[11px] tracking-[0.24em] uppercase text-[#C45C26] font-bold mb-2">The edit</p>
            <h2 className="font-display text-3xl md:text-5xl font-extrabold uppercase">{title}</h2>
          </div>
          <Link to="/products" className="hidden md:block text-sm font-semibold underline underline-offset-4 hover:text-[#C45C26]">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5 md:gap-8">
          {products.slice(0, 4).map(p => (
            <ProductCard key={p.id} {...p} />
          ))}
        </div>
        <div className="mt-12 flex justify-center md:hidden">
          <Link to="/products">
            <Button variant="outline" className="rounded-full px-16 border-stone-300">View All</Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
