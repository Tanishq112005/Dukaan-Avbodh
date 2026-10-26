import React, { useState } from "react";
import { Loader } from "../../components/ui/Loader";
import {
  User,
  Clock,
  ArrowLeft,
  Image as ImageIcon,
  Search,
  Filter,
  CheckCircle2,
  Percent,
  ShoppingBag,
  Wrench,
  Bot,
  ExternalLink,
  MessageSquare,
  Sparkles,
  ChevronRight,
  ShieldAlert,
} from "lucide-react";
import { renderMessage } from "../chatbot/renderMessage";

export function ChatTranscriptsTab({ threads, loading }) {
  const [selectedThread, setSelectedThread] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center py-28 gap-4 bg-white rounded-3xl border border-stone-200 shadow-sm">
        <Loader size="lg" />
        <p className="text-sm font-semibold text-stone-500 animate-pulse">
          Loading audited customer conversations and negotiation logs...
        </p>
      </div>
    );
  }

  if (!threads || threads.length === 0) {
    return (
      <div className="p-16 text-center bg-white border border-stone-200 rounded-3xl shadow-sm">
        <MessageSquare size={48} className="mx-auto text-stone-300 mb-3" />
        <h3 className="text-lg font-bold text-stone-800">No Audited Chat Threads Found</h3>
        <p className="text-sm text-stone-500 mt-1">
          When customers interact with the AI Shopping Assistant, conversations will appear here.
        </p>
      </div>
    );
  }

  // Filter threads
  const filteredThreads = threads.filter((t) => {
    const s = t.state || {};
    const uId = String(t.user_id || "");
    const tId = String(t.thread_id || "");
    const matchesQuery =
      uId.includes(searchQuery) ||
      tId.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesQuery) return false;

    if (filterType === "orders") {
      return Boolean(s.order_placed);
    }
    if (filterType === "negotiated") {
      return (s.negotiation_log && s.negotiation_log.length > 0) || (s.current_discount_percent > 0);
    }
    if (filterType === "discount") {
      return Number(s.current_discount_percent || 0) >= 5;
    }
    return true;
  });

  // Individual Chat View Modal/Detail
  if (selectedThread) {
    const s = selectedThread.state || {};
    const messages = selectedThread.messages || [];
    const hasProducts = s.cart_products && s.cart_products.length > 0;

    // Calculate profit
    const sellingPrice = Number(s.total_selling_price || 0);
    const discountApplied = Number(s.current_discount_percent || 0);
    const finalPrice = sellingPrice * (1 - discountApplied / 100);
    const costPrice = Number(s.total_cost_price || 0);
    const profit = Math.max(0, finalPrice - costPrice);
    const logs = s.negotiation_log || [];

    return (
      <div className="bg-[#FBF8F3] rounded-3xl border border-stone-200 shadow-xl overflow-hidden flex flex-col h-[86vh] animate-fadeIn">
        {/* Top Header Bar */}
        <div className="px-6 py-4 border-b border-stone-200 bg-white flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSelectedThread(null)}
              className="p-2.5 hover:bg-stone-100 rounded-full transition-colors bg-stone-50 border border-stone-200 text-stone-700"
              title="Back to all threads"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-black text-stone-900 text-lg">
                  Audited Customer Conversation
                </h3>
                <span className="text-xs bg-stone-100 text-stone-700 font-bold px-2.5 py-0.5 rounded-full border border-stone-200">
                  User #{selectedThread.user_id}
                </span>
                {s.order_placed && (
                  <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 size={12} /> Order Placed
                  </span>
                )}
              </div>
              <p className="text-xs text-stone-400 font-mono mt-0.5">
                Thread: {selectedThread.thread_id}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-stone-500">
              {messages.length} messages recorded
            </span>
          </div>
        </div>

        {/* Split View: Chat Conversation (Left 60%) + Financials/Audits (Right 40%) */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-12">
          {/* LEFT: Complete Conversational Messages Stream */}
          <div className="lg:col-span-7 flex flex-col border-r border-stone-200 bg-[#FBF8F3] overflow-y-auto p-6 space-y-4 custom-scrollbar">
            <div className="text-center py-2">
              <span className="text-[11px] font-bold text-stone-400 uppercase tracking-widest bg-stone-200/60 px-3 py-1 rounded-full">
                Conversation Audit Transcript
              </span>
            </div>

            {messages.length === 0 ? (
              <div className="py-20 text-center text-stone-400 text-sm">
                No conversational text messages logged in this session yet.
              </div>
            ) : (
              messages.map((msg, idx) => {
                const isHuman = msg.sender === "human" || msg.role === "human" || msg.role === "user";
                const toolCalls = msg.tool_calls || [];
                const cards = msg.cards || [];

                return (
                  <div
                    key={idx}
                    className={`flex flex-col ${isHuman ? "items-end" : "items-start"}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 text-[11px] text-stone-400">
                      {isHuman ? (
                        <>
                          <span className="font-semibold text-stone-600">Customer</span>
                          <User size={12} />
                        </>
                      ) : (
                        <>
                          <Bot size={12} className="text-orange-500" />
                          <span className="font-semibold text-stone-600">Dukaan Stylist</span>
                        </>
                      )}
                      <span>•</span>
                      <span>
                        {msg.timestamp
                          ? new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                          : "Now"}
                      </span>
                    </div>

                    {/* Message Bubble */}
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                        isHuman
                          ? "bg-black text-white rounded-tr-none"
                          : "bg-white text-stone-800 border border-stone-200/90 rounded-tl-none"
                      }`}
                    >
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {renderMessage(msg.message || msg.content || "")}
                      </div>

                      {/* Tool Calls Audit Pills */}
                      {toolCalls.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-stone-100 flex flex-col gap-1.5">
                          <p className="text-[10px] uppercase font-bold text-stone-400 flex items-center gap-1">
                            <Wrench size={11} /> Executed Backend Tools
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {toolCalls.map((tc, tIdx) => (
                              <span
                                key={tIdx}
                                className="text-xs bg-stone-100 border border-stone-200 text-stone-700 px-2.5 py-1 rounded-lg font-mono font-medium"
                              >
                                🛠️ {tc.name || "tool"}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Cards indicator */}
                      {cards.length > 0 && (
                        <div className="mt-2 text-[11px] text-orange-600 font-semibold flex items-center gap-1">
                          <Sparkles size={12} /> Dispatched {cards.length} interactive UI card(s)
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* RIGHT: Financial Audit & Haggling Details */}
          <div className="lg:col-span-5 bg-white overflow-y-auto p-6 space-y-6 custom-scrollbar border-t lg:border-t-0">
            {/* Financial Overview */}
            <div className="bg-stone-50 rounded-2xl border border-stone-200 p-5 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-4 pb-2 border-b border-stone-200 flex items-center justify-between">
                <span>Financial & Profit Audit</span>
                <span className="font-mono text-emerald-600 font-bold">
                  {profit > 0 ? `+₹${profit.toFixed(2)} Profit` : "₹0.00"}
                </span>
              </h4>

              <div className="grid grid-cols-2 gap-4 text-xs font-medium">
                <div>
                  <span className="text-stone-400 block mb-0.5">Selling Price</span>
                  <span className="font-mono text-sm font-bold text-stone-900">
                    ₹{sellingPrice.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-stone-400 block mb-0.5">Cost Price</span>
                  <span className="font-mono text-sm font-bold text-stone-900">
                    ₹{costPrice.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-stone-400 block mb-0.5">AI Discount Given</span>
                  <span className="font-mono text-sm font-bold text-purple-700">
                    {discountApplied}%
                  </span>
                </div>
                <div>
                  <span className="text-stone-400 block mb-0.5">Max Bounded Discount</span>
                  <span className="font-mono text-sm font-bold text-orange-600">
                    {s.max_discount_we_can_give || 15}%
                  </span>
                </div>
              </div>
            </div>

            {/* Negotiation Haggling Log */}
            <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center justify-between">
                <span>Negotiation Trail</span>
                <span className="text-stone-400 font-normal">{logs.length} rounds</span>
              </h4>

              {logs.length > 0 ? (
                <div className="space-y-2.5">
                  {logs.map((log, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-stone-100 bg-stone-50 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-stone-200 text-stone-700 font-bold flex items-center justify-center text-[10px]">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="font-medium text-stone-800">
                            Asked: <span className="font-bold text-black">{log.requested}%</span>
                          </p>
                          <p className="text-[11px] text-stone-500">
                            Offered: <span className="font-bold text-orange-600">{log.agent_offered}%</span>
                          </p>
                        </div>
                      </div>
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full font-bold ${
                          log.accepted
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : "bg-amber-100 text-amber-800 border border-amber-200"
                        }`}
                      >
                        {log.accepted ? "AGREED" : "COUNTERED"}
                      </span>
                    </div>
                  ))}

                  {discountApplied > 0 && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-bold flex items-center gap-1.5">
                      <CheckCircle2 size={14} className="text-emerald-600 shrink-0" />
                      Discount of {discountApplied}% verified & applied to cart!
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-stone-400 italic py-2">
                  No automated bargaining rounds recorded in this thread.
                </p>
              )}
            </div>

            {/* Products in Cart */}
            <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3">
                Items in Discussion ({s.cart_products?.length || 0})
              </h4>
              {hasProducts ? (
                <div className="space-y-2.5">
                  {s.cart_products.map((p, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-2.5 rounded-xl border border-stone-100 bg-stone-50"
                    >
                      <div className="w-11 h-11 bg-white rounded-lg overflow-hidden shrink-0 border border-stone-200">
                        {p.image_url ? (
                          <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-stone-300">
                            <ImageIcon size={16} />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-stone-800 truncate">{p.name}</p>
                        <p className="text-[11px] text-stone-500 font-mono mt-0.5">
                          ₹{p.price} • Qty {p.quantity || 1}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-stone-400 italic">No products in cart during this session.</p>
              )}
            </div>

            {/* Order Status */}
            <div className="bg-stone-50 rounded-2xl border border-stone-200 p-5 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3">
                Checkout & Payment State
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-stone-500">Order Placed:</span>
                  <span className="font-bold text-stone-900">{s.order_placed ? "Yes" : "No"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">Payment Status:</span>
                  <span className="font-bold capitalize text-stone-900">
                    {s.payment_status || "Pending"}
                  </span>
                </div>
                {s.pending_payment_link && (
                  <div className="pt-2 border-t border-stone-200">
                    <a
                      href={s.pending_payment_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-orange-600 font-bold hover:underline inline-flex items-center gap-1"
                    >
                      Razorpay Payment Link <ExternalLink size={12} />
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // List View of all threads
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-3xl border border-stone-200 shadow-sm">
        <div className="relative flex-1 max-w-md">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            type="text"
            placeholder="Search by User ID or Thread ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-black bg-stone-50/50"
          />
        </div>

        {/* Filter chips */}
        <div className="flex items-center gap-2 overflow-x-auto custom-scrollbar">
          {[
            { id: "all", label: "All Chats" },
            { id: "orders", label: "Orders Placed" },
            { id: "negotiated", label: "Negotiated" },
            { id: "discount", label: "Discounts >= 5%" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterType(f.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                filterType === f.id
                  ? "bg-black text-white shadow-sm"
                  : "bg-stone-100 text-stone-600 hover:bg-stone-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Thread Cards */}
      {filteredThreads.length === 0 ? (
        <div className="py-16 text-center text-stone-400 text-sm bg-white rounded-3xl border border-stone-200 p-8">
          No chat threads match your filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredThreads.map((thread) => {
            const s = thread.state || {};
            const msgs = thread.messages || [];
            const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;

            return (
              <div
                key={thread._id}
                onClick={() => setSelectedThread(thread)}
                className="bg-white p-6 rounded-3xl shadow-sm border border-stone-200 hover:shadow-lg transition-all duration-200 cursor-pointer hover:border-stone-900 group flex flex-col justify-between"
              >
                <div>
                  {/* Top user row */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-2xl bg-stone-100 text-stone-800 flex items-center justify-center font-black group-hover:bg-black group-hover:text-white transition-colors">
                        <User size={20} />
                      </div>
                      <div>
                        <h4 className="font-black text-stone-900 group-hover:text-orange-600 transition-colors">
                          User #{thread.user_id}
                        </h4>
                        <p
                          className="text-[11px] text-stone-400 font-mono truncate max-w-[140px]"
                          title={thread.thread_id}
                        >
                          {thread.thread_id}
                        </p>
                      </div>
                    </div>

                    {s.order_placed ? (
                      <span className="text-[11px] font-bold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                        <CheckCircle2 size={12} /> Ordered
                      </span>
                    ) : s.current_discount_percent > 0 ? (
                      <span className="text-[11px] font-bold bg-purple-100 text-purple-800 px-2.5 py-1 rounded-full border border-purple-200">
                        {s.current_discount_percent}% Off
                      </span>
                    ) : null}
                  </div>

                  {/* Snippet */}
                  <div className="bg-stone-50 rounded-2xl p-4 mb-4 border border-stone-100">
                    <p className="text-xs text-stone-600 line-clamp-2 italic">
                      "{lastMsg ? lastMsg.message || lastMsg.content : "Chat conversation started..."}"
                    </p>
                    <div className="mt-3 flex items-center gap-2 flex-wrap">
                      <span className="text-[11px] font-semibold bg-white border border-stone-200 px-2.5 py-0.5 rounded-lg text-stone-600">
                        {msgs.length} messages
                      </span>
                      {s.cart_products?.length > 0 && (
                        <span className="text-[11px] font-semibold bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-lg text-blue-700">
                          {s.cart_products.length} in cart
                        </span>
                      )}
                      {s.negotiation_log?.length > 0 && (
                        <span className="text-[11px] font-semibold bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-lg text-amber-700">
                          {s.negotiation_log.length} rounds haggled
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-stone-100 text-xs font-bold text-stone-700 group-hover:text-black">
                  <span>Inspect Audit Transcript</span>
                  <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
