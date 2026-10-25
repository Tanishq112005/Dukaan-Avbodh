import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { useStore } from "../../store/useStore";
import { ProductGallery } from "./ProductGallery";
import { ProductInfo } from "./ProductInfo";
import { Loader } from "../../components/ui/Loader";
import { productService } from "../../services/productService";
import { userEventService, EVENT_TYPES } from "../../services/userEventService";

export function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { products, addToCart: addToZustandCart, trackActivity } = useStore();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    trackActivity();
    let mounted = true;

    productService
      .getProductById(id)
      .then((data) => {
        if (mounted) {
          setProduct(data);
          setLoading(false);
          userEventService.trackEvent(EVENT_TYPES.VIEWED, data.id || id);
        }
      })
      .catch((err) => {
        console.warn("[ProductDetailPage] API fetch failed, falling back to local list:", err);
        if (mounted) {
          const fallback = products.find((p) => String(p.id) === String(id)) || {
            id: Number(id) || 1,
            name: "ONE LIFE GRAPHIC T-SHIRT",
            price: 260,
            discount: 40,
            rating: 4.5,
            brand: "ZARA",
            description:
              "This graphic t-shirt which is perfect for any occasion. Crafted from a soft and breathable fabric, it offers superior comfort and style.",
            sizes: "Small,Medium,Large,X-Large",
          };
          setProduct(fallback);
          setLoading(false);
          userEventService.trackEvent(EVENT_TYPES.VIEWED, fallback.id);
        }
      });

    return () => {
      mounted = false;
    };
  }, [id, products, trackActivity]);

  if (loading || !product) return <Loader />;

  const handleAddToCart = (qty, selSize, selColor) => {
    addToZustandCart(product, qty, selSize, selColor);
    navigate("/cart");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-stone-900 cursor-pointer">
          Home
        </Link>{" "}
        <ChevronRight className="h-4 w-4" />{" "}
        <Link to="/products" className="hover:text-stone-900 cursor-pointer">
          Shop
        </Link>{" "}
        <ChevronRight className="h-4 w-4" />{" "}
        <span className="text-black capitalize">{product.type || "T-shirts"}</span>
      </div>
      <div className="flex flex-col md:flex-row gap-10">
        <ProductGallery product={product} />
        <ProductInfo product={product} addToCart={handleAddToCart} />
      </div>
    </div>
  );
}
