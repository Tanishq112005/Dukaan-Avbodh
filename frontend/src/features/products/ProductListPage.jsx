import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { FilterSidebar } from "./FilterSidebar";
import { ProductCard } from "../../components/ui/ProductCard";
import { ChevronRight } from "lucide-react";
import { Loader } from "../../components/ui/Loader";

export function ProductListPage() {
  const { products, setProducts, searchQuery, selectedType, maxPrice } = useStore();
  const [loading, setLoading] = useState(products.length === 0);

  useEffect(() => {
    if (products.length === 0) {
      axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/product/catalog`)
        .then(res => {
          setProducts(res.data.products || res.data);
          setLoading(false);
        })
        .catch(() => {
          setProducts([
            { id: 1, name: "Gradient Graphic T-shirt", price: 145, rating: 3.5, discount: 0, type: "t-shirt", brand: "ZARA", description: "Awesome gradient t-shirt for summer.", sizes: "S,M,L" },
            { id: 2, name: "Polo with Tipping Details", price: 180, rating: 4.5, discount: 0, type: "shirt", brand: "GUCCI", description: "Classic polo shirt with tipping details.", sizes: "M,L,XL" },
            { id: 3, name: "Black Striped T-shirt", price: 120, rating: 5, discount: 30, type: "t-shirt", brand: "VERSACE", description: "Elegant black striped t-shirt.", sizes: "S,M,L,XL" },
            { id: 4, name: "Skinny Fit Jeans", price: 240, rating: 3.5, discount: 20, type: "jeans", brand: "Calvin Klein", description: "Comfortable skinny fit jeans.", sizes: "M,L" },
          ]);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return <Loader />;

  const filteredProducts = products.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === "" || p.type?.toLowerCase() === selectedType.toLowerCase();
    const matchesPrice = p.price <= maxPrice;
    return matchesSearch && matchesType && matchesPrice;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <span>Home</span> <ChevronRight className="h-4 w-4" /> <span className="text-black capitalize">{selectedType || "Products"}</span>
      </div>
      <div className="flex flex-col md:flex-row gap-8">
        <FilterSidebar />
        <div className="flex-1">
          <div className="flex justify-between items-center sticky top-[96px] bg-white z-10 py-4 pb-6">
            <h1 className="text-3xl font-bold capitalize">{selectedType || "All Products"}</h1>
            <p className="text-gray-500 text-sm">Showing {filteredProducts.length} Products</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
            {filteredProducts.map((p, i) => <ProductCard key={i} {...p} />)}
          </div>
        </div>
      </div>
    </div>
  );
}
