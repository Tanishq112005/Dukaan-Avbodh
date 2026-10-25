import { useEffect } from "react";
import { useStore } from "../../store/useStore";
import { Hero } from "./Hero";
import { ProductSection } from "./ProductSection";
import { BrowseDressStyle } from "./BrowseDressStyle";

export function HomePage() {
  const { products, fetchProducts, setProducts } = useStore();

  useEffect(() => {
    fetchProducts().catch((err) => {
      console.error("Failed to load products for homepage:", err);
      if (products.length === 0) {
        setProducts([
          { id: 1, name: "T-shirt with Tape Details", price: 120, rating: 4.5, discount: 0, type: "t-shirt", brand: "PRADA", description: "Minimalist t-shirt with elegant tape details.", sizes: "S,M,L,XL" },
          { id: 2, name: "Skinny Fit Jeans", price: 240, rating: 3.5, discount: 20, type: "jeans", brand: "Calvin Klein", description: "Comfortable skinny fit jeans.", sizes: "M,L" },
          { id: 3, name: "Checkered Shirt", price: 180, rating: 4.5, discount: 0, type: "shirt", brand: "ZARA", description: "Classic checkered shirt for casual outings.", sizes: "S,M,L" },
          { id: 4, name: "Sleeve Striped T-shirt", price: 130, rating: 4.5, discount: 30, type: "t-shirt", brand: "GUCCI", description: "Trendy striped t-shirt.", sizes: "M,L,XL" }
        ]);
      }
    });
  }, [fetchProducts, products.length, setProducts]);

  return (
    <div>
      <Hero />
      <ProductSection title="NEW ARRIVALS" products={products} />
      <hr className="max-w-7xl mx-auto border-stone-200" />
      <BrowseDressStyle />
    </div>
  );
}
