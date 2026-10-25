import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Package, ChevronRight, ShoppingBag, Clock, CheckCircle } from "lucide-react";
import { useStore } from "../../store/useStore";
import { orderService } from "../../services/orderService";
import { Loader } from "../../components/ui/Loader";

export function OrdersPage() {
  const { user, token } = useStore();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    let mounted = true;
    orderService
      .getUserOrders()
      .then((data) => {
        if (mounted) {
          setOrders(Array.isArray(data) ? data : []);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load user orders:", err);
        if (mounted) {
          setError("Could not load your orders. Please try again.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [token, navigate]);

  if (loading) return <Loader />;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-2 text-sm text-stone-400 mb-6">
        <Link to="/" className="hover:text-stone-900 cursor-pointer">Home</Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-stone-900 font-medium">My Orders</span>
      </div>

      <div className="flex justify-between items-center mb-8 border-b border-stone-200 pb-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold text-stone-900">Order History</h1>
          <p className="text-sm text-stone-500 mt-1">
            Logged in as <span className="font-semibold text-stone-800">{user?.name || user?.email}</span>
          </p>
        </div>
        <Link
          to="/products"
          className="inline-flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white text-sm px-4 py-2 rounded-full transition-colors"
        >
          <ShoppingBag className="w-4 h-4" />
          <span>Continue Shopping</span>
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm mb-6 border border-red-200">
          {error}
        </div>
      )}

      {orders.length === 0 ? (
        <div className="text-center py-16 bg-white border border-stone-200 rounded-3xl p-8 shadow-sm">
          <div className="w-16 h-16 bg-stone-100 rounded-full flex items-center justify-center mx-auto mb-4 text-stone-400">
            <Package className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-stone-900 mb-2">No orders placed yet</h2>
          <p className="text-stone-500 text-sm max-w-sm mx-auto mb-6">
            Browse our catalog, negotiate custom discounts with our AI atelier assistant, and place your first order.
          </p>
          <Link
            to="/products"
            className="inline-flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white font-medium px-6 py-3 rounded-full text-sm"
          >
            Explore Catalog
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order, idx) => (
            <div
              key={order.id || idx}
              className="bg-white border border-stone-200 rounded-2xl p-6 shadow-sm hover:border-stone-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono font-bold text-stone-900 text-sm">
                    Order #{order.id}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-medium ${
                      order.status === "paid" || order.status === "confirmed" || order.status === "completed"
                        ? "bg-green-100 text-green-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {order.status === "paid" || order.status === "confirmed" ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : (
                      <Clock className="w-3 h-3" />
                    )}
                    <span className="capitalize">{order.status || "Pending"}</span>
                  </span>
                </div>

                <p className="text-sm text-stone-700">
                  {order.product?.name ? (
                    <span className="font-medium">{order.product.name}</span>
                  ) : (
                    <span>Product ID #{order.product_id || "N/A"}</span>
                  )}{" "}
                  <span className="text-stone-400">&times; {order.quantity || 1}</span>
                </p>

                {order.created_at && (
                  <p className="text-xs text-stone-400">
                    Placed on {new Date(order.created_at).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                )}
              </div>

              <div className="flex md:flex-col items-end justify-between md:justify-center border-t md:border-t-0 pt-3 md:pt-0 border-stone-100">
                {order.discount_applied > 0 && (
                  <span className="text-xs text-emerald-600 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full mb-1">
                    {order.discount_applied}% AI Discount Applied
                  </span>
                )}
                {order.product?.price && (
                  <span className="font-bold text-lg text-stone-900">
                    ₹{(
                      (order.product.price * (order.quantity || 1)) *
                      (1 - (order.discount_applied || 0) / 100)
                    ).toFixed(0)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
