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
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-7">
      {/* Clean Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-stone-400 mb-5">
        <Link to="/" className="hover:text-stone-900 transition-colors cursor-pointer">
          Home
        </Link>
        <ChevronRight className="h-3 w-3 text-stone-300" />
        <Link to="/products" className="hover:text-stone-900 transition-colors cursor-pointer">
          Shop
        </Link>
        <ChevronRight className="h-3 w-3 text-stone-300" />
        <span className="text-stone-800 font-medium capitalize truncate max-w-[200px]">
          {product.type || "Apparel"}
        </span>
      </nav>

      {/* Main Two-Column Showcase: Sticky Gallery + Refined Info */}
      <div className="flex flex-col md:flex-row items-start gap-8 lg:gap-12">
        <div className="w-full md:w-[44%] lg:w-[42%] md:sticky md:top-24 flex-shrink-0">
          <ProductGallery product={product} />
        </div>
        <div className="w-full md:w-[56%] lg:w-[58%] flex-1 min-w-0">
          <ProductInfo product={product} addToCart={handleAddToCart} />
        </div>
      </div>
    </div>
  );
}
