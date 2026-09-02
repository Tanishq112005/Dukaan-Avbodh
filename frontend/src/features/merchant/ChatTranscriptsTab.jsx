import React, { useState } from "react";
import { Loader } from "../../components/ui/Loader";
import { User, Clock, ArrowLeft, Image as ImageIcon } from "lucide-react";

export function ChatTranscriptsTab({ threads, loading }) {
  const [selectedThread, setSelectedThread] = useState(null);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader size="lg" />
      </div>
    );
  }

  if (!threads || threads.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500 bg-white border border-gray-100 rounded-2xl shadow-sm">
        No chat transcripts found.
      </div>
    );
  }

  // Individual Chat View Modal/Detail
  if (selectedThread) {
    const s = selectedThread.state || {};
    const hasProducts = s.cart_products && s.cart_products.length > 0;

    // Calculate profit
    const sellingPrice = s.total_selling_price || 0;
    const discountApplied = s.current_discount_percent || 0;
    const finalPrice = sellingPrice * (1 - discountApplied / 100);
    const costPrice = s.total_cost_price || 0;
    const profit = Math.max(0, finalPrice - costPrice);

    const logs = s.negotiation_log || [];

    return (
      <div className="bg-[#FBF8F3] rounded-2xl border border-stone-200 shadow-lg overflow-hidden flex flex-col h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-200 bg-white flex items-center gap-4">
          <button
            onClick={() => setSelectedThread(null)}
            className="p-2 hover:bg-stone-100 rounded-full transition-colors bg-stone-50"
          >
            <ArrowLeft size={20} className="text-stone-600" />
          </button>
          <div>
            <h3 className="font-bold text-stone-900 text-lg">
              Detailed Thread Analysis
            </h3>
            <p className="text-xs text-stone-500 font-mono mt-0.5">
              ID: {selectedThread.thread_id}
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          {/* Top Section: Overview */}
          <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
            <h4 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-4 border-b pb-2">
              Customer & Financials
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-y-4 gap-x-6 text-sm">
              <div>
                <span className="text-stone-500">User ID:</span>{" "}
                <span className="font-mono font-medium">
                  {selectedThread.user_id}
                </span>
              </div>
              <div>
                <span className="text-stone-500">Name:</span>{" "}
                <span className="font-medium">
                  {s.user_info?.name || "Unknown"}
                </span>
              </div>
              <div>
                <span className="text-stone-500">Email:</span>{" "}
                <span className="font-medium">
                  {s.user_info?.email || "Unknown"}
                </span>
              </div>

              <div className="col-span-2 md:col-span-4 border-t my-1"></div>

              <div>
                <span className="text-stone-500">Cost Price:</span>{" "}
                <span className="font-mono">₹{costPrice.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-stone-500">Selling Price:</span>{" "}
                <span className="font-mono">₹{sellingPrice.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-stone-500">
                  Max Discount We Can Give:
                </span>{" "}
                <span className="font-bold text-orange-600 font-mono">
                  {s.max_discount_we_can_give || 0}%
                </span>
              </div>

              <div>
                <span className="text-stone-500">Discount Applied:</span>{" "}
                <span className="font-mono">{discountApplied}%</span>
              </div>
              <div>
                <span className="text-stone-500">Profit:</span>{" "}
                <span className="font-mono font-bold text-emerald-600">
                  ₹{profit.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Product Details (Horizontal Scroll) */}
          <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
            <h4 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-4 border-b pb-2">
              Product Details
            </h4>
            {hasProducts ? (
              <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
                {s.cart_products.map((p, idx) => (
                  <div
                    key={idx}
                    className="min-w-[140px] max-w-[140px] border border-stone-100 rounded-lg overflow-hidden shrink-0 shadow-sm"
                  >
                    {p.image_url ? (
                      <img
                        src={p.image_url}
                        alt={p.name}
                        className="w-full h-32 object-cover bg-stone-50"
                      />
                    ) : (
                      <div className="w-full h-32 bg-stone-100 flex items-center justify-center text-stone-400">
                        <ImageIcon size={24} />
                      </div>
                    )}
                    <div className="p-2.5">
                      <p className="text-xs font-semibold text-stone-800 line-clamp-1">
                        {p.name}
                      </p>
                      <p className="text-xs text-stone-500 mt-1 font-mono">
                        ₹{p.price}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-500 italic">
                No products associated with this negotiation round.
              </p>
            )}
          </div>

          {/* Applied Campaigns Section */}
          <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
            <h4 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-4 border-b pb-2">
              Applied Campaigns (Pre-Negotiation)
            </h4>
            {s.applied_campaigns && s.applied_campaigns.length > 0 ? (
              <div className="flex flex-col gap-3">
                {s.applied_campaigns.map((camp, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-purple-100 bg-purple-50 gap-2">
                    <div className="flex items-center gap-2">
                      <div className="bg-purple-200 text-purple-700 font-bold text-xs rounded-full px-2 py-1 flex items-center justify-center shrink-0">
                        {camp.type || "CAMPAIGN"}
                      </div>
                      <p className="text-sm font-semibold text-stone-800">
                        {camp.agenda || `Campaign ID: ${camp.campaign_id}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 ml-8 sm:ml-0">
                      <p className="text-sm text-stone-700">
                        Discount Stacked:{" "}
                        <span className="font-bold text-purple-700">
                          {camp.discount_percentage}%
                        </span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-500 italic">
                No campaigns were active for these products.
              </p>
            )}
          </div>

          {/* Negotiation Log */}
          <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
            <h4 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-4 border-b pb-2">
              Discussion & Negotiation Log
            </h4>

            {logs.length > 0 ? (
              <div className="flex flex-col gap-3">
                {logs.map((log, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg border border-stone-100 bg-stone-50 gap-2"
                  >
                    <div className="flex items-center gap-2">
                      <div className="bg-stone-200 text-stone-600 font-bold text-xs rounded-full w-6 h-6 flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <p className="text-sm text-stone-700">
                        User asked for{" "}
                        <span className="font-bold text-black">
                          {log.requested}%
                        </span>{" "}
                        discount
                      </p>
                    </div>
                    <div className="flex items-center gap-3 ml-8 sm:ml-0">
                      <p className="text-sm text-stone-700">
                        Agent gave{" "}
                        <span className="font-bold text-orange-600">
                          {log.agent_offered}%
                        </span>
                      </p>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-bold ${log.accepted ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}
                      >
                        {log.accepted ? "ACCEPTED" : "NOT ACCEPTED"}
                      </span>
                    </div>
                  </div>
                ))}
                {discountApplied > 0 && (
                  <div className="mt-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-sm font-semibold flex items-center">
                    🎉 Discount of {discountApplied}% is confirmed!
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-stone-500 italic">
                No haggling recorded in this thread.
              </p>
            )}
          </div>

          {/* Order Info */}
          <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm mb-8">
            <h4 className="text-sm font-bold uppercase tracking-wider text-stone-400 mb-4 border-b pb-2">
              Order Details
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-stone-500 mb-1">Order Placed</p>
                <p className="font-semibold">{s.order_placed ? "Yes" : "No"}</p>
              </div>
              <div>
                <p className="text-stone-500 mb-1">Razorpay ID</p>
                <p className="font-mono font-medium">
                  {s.razorpay_id || "N/A"}
                </p>
              </div>
              <div>
                <p className="text-stone-500 mb-1">Payment Status</p>
                <p className="font-semibold capitalize">
                  {s.payment_status || "Pending"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // List View
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {threads.map((thread) => (
        <div
          key={thread._id}
          onClick={() => setSelectedThread(thread)}
          className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer hover:border-orange-300 group flex flex-col"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-orange-100 p-2.5 rounded-full text-orange-600">
                <User size={20} />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">
                  User {thread.user_id}
                </h3>
                <p
                  className="text-[10px] text-gray-400 font-mono mt-0.5 truncate max-w-[120px]"
                  title={thread.thread_id}
                >
                  {thread.thread_id}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-xl p-4 mb-4 flex-1">
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold bg-white border border-gray-200 px-2 py-1 rounded text-gray-600">
                {thread.state?.cart_products?.length || 0} Products
              </span>
              <span className="text-xs font-semibold bg-blue-50 border border-blue-200 px-2 py-1 rounded text-blue-700">
                {thread.state?.negotiation_log?.length || 0} Negotiated
              </span>
              {thread.state?.current_discount_percent > 0 && (
                <span className="text-xs font-semibold bg-green-50 border border-green-200 px-2 py-1 rounded text-green-700">
                  {thread.state.current_discount_percent}% Discount
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center text-sm font-semibold text-orange-600 group-hover:text-orange-700">
            View Details{" "}
            <ArrowLeft
              size={16}
              className="ml-1 rotate-180 group-hover:translate-x-1 transition-transform"
            />
          </div>
        </div>
      ))}
    </div>
  );
}
