import React, { useState } from "react";
import { Loader } from "../../components/ui/Loader";
import {
  ShoppingBag,
  Package,
  User,
  Clock,
  CheckCircle2,
  Truck,
  MapPin,
  ExternalLink,
  Copy,
  Search,
} from "lucide-react";

export function OrdersTab({ orders, loading }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center py-28 gap-4 bg-white rounded-3xl border border-stone-200 shadow-sm">
        <Loader size="lg" />
        <p className="text-sm font-semibold text-stone-500 animate-pulse">
          Loading merchant orders and fulfillment pipeline...
        </p>
      </div>
    );
  }

  const filteredOrders = (orders || []).filter((o) => {
    const q = searchQuery.toLowerCase();
    const idStr = String(o.id || o.order_id || "");
    const custName = String(o.user?.name || "").toLowerCase();
    const custEmail = String(o.user?.email || "").toLowerCase();
    const rz = String(o.razorpay_order_id || "").toLowerCase();
    return idStr.includes(q) || custName.includes(q) || custEmail.includes(q) || rz.includes(q);
  });

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* Top Header Card */}
      <div className="bg-stone-900 text-white p-3.5 sm:px-4 sm:py-2.5 rounded-2xl shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <ShoppingBag size={18} className="text-[#C45C26]" />
          <div>
            <h2 className="text-sm font-bold tracking-tight text-white">Recent Live Orders</h2>
            <p className="text-[10px] text-stone-400">
              Confirmed customer checkouts with AI negotiated discount breakdowns
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono font-bold bg-white/10 px-2.5 py-1 rounded-lg self-start sm:self-auto border border-white/10">
          {filteredOrders.length} Orders
        </span>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" />
        <input
          type="text"
          placeholder="Search by order ID, customer name, email..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-11 pr-4 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-black bg-white shadow-sm"
        />
      </div>

      {filteredOrders.length === 0 ? (
        <div className="p-16 text-center bg-white border border-stone-200 rounded-3xl shadow-sm text-stone-400 text-sm">
          <ShoppingBag size={48} className="mx-auto text-stone-300 mb-3" />
          <p className="font-bold text-stone-700">No matching orders found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredOrders.map((order) => {
            const st = String(order.payment_status || order.status || "confirmed").toLowerCase();
            const isDelivered = st === "delivered";
            const isShipped = st === "shipped";
            const isPaid = st === "paid" || st === "confirmed";

            return (
              <div
                key={order.id}
                className="border border-stone-200 rounded-3xl p-6 bg-white shadow-sm hover:shadow-lg transition-all duration-200 flex flex-col justify-between"
              >
                <div>
                  {/* Top Header: Order ID & Status */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono font-bold text-stone-900 text-sm">
                      #{order.id}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase tracking-wider flex items-center gap-1 ${
                        isDelivered
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : isShipped
                          ? "bg-blue-100 text-blue-800 border border-blue-200"
                          : isPaid
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      <CheckCircle2 size={12} />
                      {order.payment_status || order.status || "CONFIRMED"}
                    </span>
                  </div>

                  {/* Products preview */}
                  <div className="space-y-3 mb-4">
                    {order.products?.map((prod, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-3 p-2.5 rounded-2xl bg-stone-50 border border-stone-100"
                      >
                        <div className="w-12 h-14 bg-white rounded-xl overflow-hidden shrink-0 border border-stone-200">
                          {prod.image_url ? (
                            <img
                              src={prod.image_url}
                              alt={prod.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-stone-300">
                              <Package size={18} />
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-stone-900 text-xs truncate">
                            {prod.name}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs font-mono font-bold text-stone-700">
                              ₹{prod.price}
                            </span>
                            <span className="text-[11px] text-stone-400 font-medium">
                              Qty: {prod.quantity || 1}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Financial & Discount badge */}
                  <div className="flex items-center justify-between p-3 rounded-2xl bg-stone-100/70 mb-4 text-xs">
                    <div>
                      <span className="text-stone-500 block text-[11px]">AI Discount</span>
                      <span className="font-bold text-purple-700 font-mono">
                        {order.discount_applied || 0}% Off
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-stone-500 block text-[11px]">Total Paid</span>
                      <span className="font-black text-stone-900 font-mono text-sm">
                        ₹{Number(order.total_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  {/* Customer Information */}
                  <div className="bg-stone-50 p-3.5 rounded-2xl border border-stone-100 space-y-1.5 text-xs text-stone-600 mb-4">
                    <p className="flex items-center gap-2">
                      <User size={13} className="text-stone-400 shrink-0" />
                      <strong className="text-stone-900">{order.user?.name || "Customer"}</strong>
                    </p>
                    <p className="text-stone-500 truncate pl-5">
                      {order.user?.email || "customer@dukaan.local"}
                    </p>
                    <p className="flex items-start gap-2 pt-1 border-t border-stone-200/60 text-[11px] text-stone-500">
                      <MapPin size={13} className="text-stone-400 shrink-0 mt-0.5" />
                      <span className="line-clamp-2">{order.user?.address || "Bangalore, India"}</span>
                    </p>
                  </div>
                </div>

                {/* Footer Gateway metadata */}
                <div className="pt-3 border-t border-stone-100 space-y-1 text-[11px] text-stone-400 font-mono">
                  <div className="flex items-center justify-between">
                    <span className="truncate max-w-[200px]" title={order.razorpay_order_id}>
                      Rzp: {order.razorpay_order_id || "N/A"}
                    </span>
                    {order.razorpay_order_id && (
                      <button
                        onClick={() => copyToClipboard(order.razorpay_order_id, order.id)}
                        className="text-stone-500 hover:text-black transition"
                        title="Copy Gateway Order ID"
                      >
                        <Copy size={12} />
                      </button>
                    )}
                  </div>
                  <div className="flex items-center justify-between text-stone-400 text-[10px]">
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {order.created_at ? new Date(order.created_at).toLocaleString() : "Recent"}
                    </span>
                    {copiedId === order.id && (
                      <span className="text-emerald-600 font-bold">Copied!</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
