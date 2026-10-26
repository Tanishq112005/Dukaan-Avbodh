import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Package,
  ChevronRight,
  ShoppingBag,
  Clock,
  CheckCircle,
  XCircle,
  Truck,
  ExternalLink,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { useStore } from "../../store/useStore";
import { orderService } from "../../services/orderService";
import { Loader } from "../../components/ui/Loader";

export function OrdersPage() {
  const { user, token } = useStore();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancellingId, setCancellingId] = useState(null);
  const [trackingData, setTrackingData] = useState(null);
  const [trackingLoadingId, setTrackingLoadingId] = useState(null);

  const fetchOrders = async () => {
    try {
      setError("");
      const data = await orderService.getUserOrders();
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load user orders:", err);
      setError("Could not load your orders. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    fetchOrders();
  }, [token, navigate]);

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm(`Are you sure you want to cancel Order #${orderId}? Your reserved stock will be released.`)) {
      return;
    }
    setCancellingId(orderId);
    try {
      const res = await orderService.cancelOrder(orderId);
      if (res && res.success) {
        // Optimistically update order status in list
        setOrders((prev) =>
          prev.map((o) => {
            const currentId = o.order_id || o.id;
            if (currentId === orderId) {
              return {
                ...o,
                payment_status: "cancelled",
                status: "cancelled",
                tracking_status: "cancelled",
                stage: "Cancelled",
              };
            }
            return o;
          })
        );
      }
    } catch (err) {
      console.error("Failed to cancel order:", err);
      alert(err.response?.data?.detail || "Could not cancel order. It may have already been dispatched.");
    } finally {
      setCancellingId(null);
    }
  };

  const handleTrackOrder = async (orderId) => {
    setTrackingLoadingId(orderId);
    try {
      const res = await orderService.trackOrder(orderId);
      if (res && res.success) {
        setTrackingData(res);
      } else {
        alert(res?.error || "Could not fetch tracking details.");
      }
    } catch (err) {
      console.error("Tracking error:", err);
      alert("Failed to track order status. Please try again.");
    } finally {
      setTrackingLoadingId(null);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-stone-400 mb-6">
        <Link to="/" className="hover:text-stone-900 cursor-pointer">Home</Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-stone-900 font-medium">My Orders</span>
      </div>

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8 border-b border-stone-200 pb-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold text-stone-900">Order History</h1>
          <p className="text-sm text-stone-500 mt-1">
            Logged in as <span className="font-semibold text-stone-800">{user?.name || user?.email}</span>
          </p>
        </div>
        <Link
          to="/products"
          className="inline-flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white text-sm px-5 py-2.5 rounded-full transition-colors shadow-xs"
        >
          <ShoppingBag className="w-4 h-4" />
          <span>Continue Shopping</span>
        </Link>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm mb-6 border border-red-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Empty State */}
      {orders.length === 0 ? (
        <div className="text-center py-16 bg-white border border-stone-200 rounded-3xl p-8 shadow-sm">
          <div className="w-16 h-16 bg-stone-100 rounded-full flex items-center justify-center mx-auto mb-4 text-stone-400">
            <Package className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-stone-900 mb-2">No orders placed yet</h2>
          <p className="text-stone-500 text-sm max-w-sm mx-auto mb-6 leading-relaxed">
            Browse our curated collections, negotiate tailored discounts with our AI stylist, and place your first order.
          </p>
          <Link
            to="/products"
            className="inline-flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white font-medium px-6 py-3 rounded-full text-sm transition-colors shadow-sm"
          >
            Explore Catalog
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order, idx) => {
            const orderId = order.order_id || order.id;
            const status = (order.payment_status || order.status || "pending").toLowerCase();
            const isPaid = status === "paid" || status === "confirmed" || status === "completed";
            const isCancelled = status === "cancelled" || status === "refunded";
            const canCancel = !isCancelled && (status === "pending" || status === "pending_payment" || status === "processing" || status === "placed");
            const product = order.product || {};
            const finalPrice = order.total_amount !== undefined && order.total_amount !== null
              ? Number(order.total_amount)
              : product.price
              ? (Number(product.price) * (order.quantity || 1)) * (1 - (order.discount_applied || 0) / 100)
              : 0;

            const imgUrl =
              product.image_url ||
              (product.id ? `https://picsum.photos/seed/${product.id}/200/250` : "https://picsum.photos/seed/dukaan/200/250");

            return (
              <div
                key={orderId || idx}
                className="bg-white border border-stone-200/90 rounded-2xl p-5 sm:p-6 shadow-xs hover:border-stone-300 transition-all flex flex-col gap-4"
              >
                {/* Top Row: Order ID, Status, Date */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-stone-100">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono font-bold text-stone-900 text-sm">
                      Order #{orderId}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        isPaid
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : isCancelled
                          ? "bg-stone-100 text-stone-600 border border-stone-200"
                          : "bg-amber-50 text-amber-800 border border-amber-200"
                      }`}
                    >
                      {isPaid ? (
                        <CheckCircle className="w-3 h-3 text-emerald-600" />
                      ) : isCancelled ? (
                        <XCircle className="w-3 h-3 text-stone-500" />
                      ) : (
                        <Clock className="w-3 h-3 text-amber-600" />
                      )}
                      <span>{status}</span>
                    </span>
                  </div>

                  {order.created_at && (
                    <span className="text-xs text-stone-400">
                      {new Date(order.created_at).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  )}
                </div>

                {/* Middle Row: Product info and pricing */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3.5">
                    <Link
                      to={product.id ? `/product/${product.id}` : "#"}
                      className="w-16 h-18 rounded-xl bg-stone-100 overflow-hidden flex-shrink-0 border border-stone-200 block"
                    >
                      <img
                        src={imgUrl}
                        alt={product.name || "Product"}
                        className="w-full h-full object-cover"
                      />
                    </Link>

                    <div>
                      {product.brand && (
                        <span className="text-[10px] font-bold uppercase tracking-wider text-stone-400">
                          {product.brand}
                        </span>
                      )}
                      <Link
                        to={product.id ? `/product/${product.id}` : "#"}
                        className="text-sm font-semibold text-stone-900 hover:text-[#C45C26] transition-colors block line-clamp-1"
                      >
                        {product.name || `Product Item #${order.product_id}`}
                      </Link>
                      <div className="flex items-center gap-2 text-xs text-stone-500 mt-0.5">
                        <span>Qty: <strong className="text-stone-800">{order.quantity || 1}</strong></span>
                        {order.discount_applied > 0 && (
                          <span className="text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.2 rounded-xs text-[10px]">
                            {order.discount_applied}% Discount
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Pricing */}
                  <div className="text-right sm:self-center">
                    <span className="text-xs text-stone-400 block font-medium">Order Total</span>
                    <span className="font-display font-extrabold text-xl text-stone-900">
                      ₹{Math.round(finalPrice).toLocaleString("en-IN")}
                    </span>
                  </div>
                </div>

                {/* Bottom Row: Actions (Track, Pay Now, Cancel) */}
                <div className="flex flex-wrap items-center justify-end gap-2 pt-3 border-t border-stone-100">
                  {/* Track Order Button */}
                  <button
                    type="button"
                    onClick={() => handleTrackOrder(orderId)}
                    disabled={trackingLoadingId === orderId}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-200 bg-white hover:bg-stone-50 text-stone-800 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Truck size={13} className="text-[#C45C26]" />
                    <span>{trackingLoadingId === orderId ? "Tracking..." : "Track Order"}</span>
                  </button>

                  {/* Pending Payment URL Link */}
                  {!isPaid && !isCancelled && order.payment_link_url && (
                    <a
                      href={order.payment_link_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C45C26] hover:bg-[#a3471a] text-white text-xs font-bold transition-colors cursor-pointer"
                    >
                      <span>Pay Now</span>
                      <ExternalLink size={12} />
                    </a>
                  )}

                  {/* Cancel Order Button */}
                  {canCancel && (
                    <button
                      type="button"
                      onClick={() => handleCancelOrder(orderId)}
                      disabled={cancellingId === orderId}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold transition-colors cursor-pointer"
                    >
                      <RotateCcw size={12} />
                      <span>{cancellingId === orderId ? "Cancelling..." : "Cancel Order"}</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Live Order Tracking Modal */}
      {trackingData && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-stone-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-stone-100">
              <div className="flex items-center gap-2">
                <Truck size={18} className="text-[#C45C26]" />
                <h3 className="font-bold text-stone-900 text-base">Live Order Tracking</h3>
              </div>
              <button
                type="button"
                onClick={() => setTrackingData(null)}
                className="text-stone-400 hover:text-stone-700 text-sm p-1 rounded-md"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-stone-500 mb-4">
              Tracking Order <strong className="text-stone-900">#{trackingData.order_id}</strong>
            </div>

            {/* Progress Timeline Stepper */}
            <div className="my-6 px-2">
              <div className="flex items-center justify-between relative">
                <div className="absolute left-2 right-2 top-2.5 h-0.5 bg-stone-200 -z-0" />
                {[
                  { label: "Placed", done: true },
                  { label: "Quality Check", done: trackingData.status !== "placed" },
                  { label: "Dispatched", done: trackingData.status === "shipped" || trackingData.status === "out_for_delivery" || trackingData.status === "delivered" },
                  { label: "Delivered", done: trackingData.status === "delivered" },
                ].map((step, idx) => (
                  <div key={idx} className="flex flex-col items-center relative z-10">
                    <div
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                        step.done
                          ? "bg-emerald-600 text-white shadow-xs"
                          : "bg-white border-2 border-stone-300 text-stone-400"
                      }`}
                    >
                      {step.done ? <CheckCircle2 size={12} /> : idx + 1}
                    </div>
                    <span className={`text-[10px] mt-1.5 font-semibold ${step.done ? "text-stone-900" : "text-stone-400"}`}>
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Estimated Delivery Box */}
            <div className="bg-stone-50 rounded-2xl p-3 border border-stone-200 flex items-center justify-between text-xs mb-5">
              <div className="flex items-center gap-2 text-stone-700">
                <Clock size={14} className="text-emerald-700" />
                <span>{trackingData.delivery_estimate || "3-5 Business Days"}</span>
              </div>
              <span className="text-[10px] font-bold uppercase text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                {trackingData.stage || trackingData.status}
              </span>
            </div>

            <button
              type="button"
              onClick={() => setTrackingData(null)}
              className="w-full py-2.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-white text-xs font-bold uppercase tracking-wider transition-colors"
            >
              Close Tracking
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
