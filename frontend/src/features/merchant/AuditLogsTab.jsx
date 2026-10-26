import React, { useState } from "react";
import { Loader } from "../../components/ui/Loader";
import {
  ShieldCheck,
  Search,
  Filter,
  Clock,
  User,
  Percent,
  ShoppingCart,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Package,
} from "lucide-react";

export function AuditLogsTab({ logs, loading, error }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterAction, setFilterAction] = useState("all");

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center py-28 gap-4 bg-white rounded-3xl border border-stone-200 shadow-sm">
        <Loader size="lg" />
        <p className="text-sm font-semibold text-stone-500 animate-pulse">
          Loading immutable security audits and negotiation bounds logs...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center bg-red-50 border border-red-200 rounded-3xl text-red-700">
        <AlertCircle size={32} className="mx-auto mb-2 text-red-500" />
        <p className="font-bold">{error}</p>
      </div>
    );
  }

  const filteredLogs = (logs || []).filter((log) => {
    const act = String(log.action || "").toLowerCase();
    const reason = String(log.reason || "").toLowerCase();
    const result = String(log.result || "").toLowerCase();
    const uId = String(log.user_id || "");
    const q = searchQuery.toLowerCase();

    const matchesSearch =
      act.includes(q) || reason.includes(q) || result.includes(q) || uId.includes(q);

    if (!matchesSearch) return false;

    if (filterAction === "negotiation") {
      return act.includes("discount") || act.includes("negotiation") || act.includes("deal");
    }
    if (filterAction === "order") {
      return act.includes("order") || act.includes("checkout");
    }
    if (filterAction === "cart") {
      return act.includes("cart");
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header Card */}
      <div className="bg-stone-900 text-white p-7 rounded-3xl shadow-lg shadow-stone-950/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck size={24} className="text-emerald-400" />
            <h2 className="text-xl font-black tracking-tight">Security & Financial Audit Trail</h2>
          </div>
          <p className="text-xs text-stone-400 mt-1 max-w-xl">
            Immutable log of all AI automated decisions, discount bound enforcements, cart modifications, and payment events.
          </p>
        </div>
        <span className="text-xs font-mono font-bold bg-white/10 px-3.5 py-1.5 rounded-xl self-start sm:self-auto border border-white/10">
          {filteredLogs.length} Events Audited
        </span>
      </div>

      {/* Controls & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-3xl border border-stone-200 shadow-sm">
        <div className="relative flex-1 max-w-md">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            type="text"
            placeholder="Search by action, user ID, or reasoning..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 rounded-2xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-black bg-stone-50/50"
          />
        </div>

        {/* Action Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto custom-scrollbar">
          {[
            { id: "all", label: "All Audits" },
            { id: "negotiation", label: "AI Bargaining" },
            { id: "order", label: "Orders" },
            { id: "cart", label: "Cart Activity" },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterAction(f.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                filterAction === f.id
                  ? "bg-black text-white shadow-sm"
                  : "bg-stone-100 text-stone-600 hover:bg-stone-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Cards Grid */}
      {filteredLogs.length === 0 ? (
        <div className="py-16 text-center text-stone-400 text-sm bg-white rounded-3xl border border-stone-200 p-8">
          No audit entries matching your search filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredLogs.map((log) => {
            const isNegotiation = String(log.action || "").includes("DISCOUNT") || String(log.action || "").includes("NEGOTIATION");
            const isOrder = String(log.action || "").includes("ORDER");

            return (
              <div
                key={log._id}
                className="bg-white p-6 rounded-3xl border border-stone-200 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Action Tag & Time */}
                  <div className="flex items-center justify-between gap-2 mb-4">
                    <span
                      className={`text-xs font-mono font-bold px-3 py-1 rounded-xl uppercase tracking-wider ${
                        isNegotiation
                          ? "bg-purple-100 text-purple-800 border border-purple-200"
                          : isOrder
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : "bg-stone-100 text-stone-800 border border-stone-200"
                      }`}
                    >
                      {log.action}
                    </span>
                    <span className="text-[11px] font-semibold text-stone-400 flex items-center gap-1">
                      <Clock size={12} />
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : "Recent"}
                    </span>
                  </div>

                  {/* Reasoning Box */}
                  <div className="bg-stone-50 rounded-2xl p-4 mb-3 border border-stone-100">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-stone-400 mb-1">
                      Policy Enforcement & Reasoning
                    </p>
                    <p className="text-xs text-stone-800 leading-relaxed font-medium">
                      {log.reason || "System bound check passed."}
                    </p>
                  </div>

                  {/* Outcome Result */}
                  <div className="p-3.5 rounded-2xl bg-emerald-50/70 border border-emerald-100 mb-3 flex items-start gap-2.5">
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[10px] font-bold uppercase text-emerald-800">Result</p>
                      <p className="text-xs font-bold text-emerald-950 font-mono">
                        {log.result}
                      </p>
                    </div>
                  </div>

                  {/* Products involved (if available) */}
                  {log.metadata?.products && log.metadata.products.length > 0 && (
                    <div className="bg-stone-50/70 p-3 rounded-2xl border border-stone-100 mb-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-stone-400 mb-2">
                        Target Products ({log.metadata.products.length})
                      </p>
                      <div className="flex flex-col gap-2">
                        {log.metadata.products.slice(0, 3).map((p, pIdx) => (
                          <div key={pIdx} className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg overflow-hidden bg-white border shrink-0">
                              {p.image_url ? (
                                <img src={p.image_url} alt={p.name} className="w-full h-full object-cover" />
                              ) : (
                                <div className="w-full h-full bg-stone-200" />
                              )}
                            </div>
                            <div className="overflow-hidden">
                              <p className="text-xs font-semibold text-stone-800 truncate">{p.name}</p>
                              <p className="text-[10px] text-stone-500 font-mono">₹{p.price}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer User Info */}
                <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
                  <span className="font-mono">User ID: #{log.user_id || "guest"}</span>
                  {log.thread_id && (
                    <span className="font-mono truncate max-w-[150px]" title={log.thread_id}>
                      Thread: {log.thread_id}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
