import { useParams, useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { useStore } from "../../store/useStore";
import { ProductGallery } from "./ProductGallery";
import { ProductInfo } from "./ProductInfo";

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { products, addToCart: addToZustandCart } = useStore();
  
  const product = products.find(p => p.id == id) || {
    id, name: "ONE LIFE GRAPHIC T-SHIRT", price: 260, discount: 40, rating: 4.5, brand: "ZARA",
    description: "This graphic t-shirt which is perfect for any occasion. Crafted from a soft and breathable fabric, it offers superior comfort and style.",
    sizes: "Small,Medium,Large,X-Large"
  };

  const handleAddToCart = (qty, selSize, selColor) => {
    addToZustandCart(product, qty, selSize, selColor);
    navigate("/cart");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <span>Home</span> <ChevronRight className="h-4 w-4" /> <span>Shop</span> <ChevronRight className="h-4 w-4" /> <span className="text-black capitalize">{product.type || "T-shirts"}</span>
      </div>
      <div className="flex flex-col md:flex-row gap-10">
        <ProductGallery product={product} />
        <ProductInfo product={product} addToCart={handleAddToCart} />
      </div>
    </div>
  );
}
