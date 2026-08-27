import { ProductCard } from "../../components/ui/ProductCard";
import { Button } from "../../components/ui/button";

export function ProductSection({ title, products }) {
  return (
    <section className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-black text-center mb-12 uppercase">{title}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          {products.slice(0, 4).map(p => (
            <ProductCard key={p.id} {...p} />
          ))}
        </div>
        <div className="mt-10 flex justify-center">
          <Button variant="outline" className="rounded-full px-16">View All</Button>
        </div>
      </div>
    </section>
  );
}
