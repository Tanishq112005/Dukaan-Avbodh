import React, { useState } from "react";
import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";
import { MerchantAnalytics } from "./MerchantAnalytics";
import { MerchantTabs } from "./MerchantTabs";
import { AuditLogsTab } from "./AuditLogsTab";
import { OrdersTab } from "./OrdersTab";
import { ChatTranscriptsTab } from "./ChatTranscriptsTab";
import { useMerchantData } from "./useMerchantData";
import { MerchantAgentTab } from "./MerchantAgentTab";
import {
  Sparkles,
  ShieldCheck,
  Zap,
  Lock,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [activeTab, setActiveTab] = useState("analytics");
  const { logs, orders, threads, loading, error } = useMerchantData();

  if (!token) {
    return (
      <div className="max-w-md mx-auto my-24 p-8 text-center bg-white rounded-3xl border border-stone-200 shadow-xl">
        <div className="w-14 h-14 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Lock size={28} />
        </div>
        <h2 className="text-2xl font-black text-stone-900 mb-2">Merchant Authentication Required</h2>
        <p className="text-sm text-stone-500 mb-6">
          Please log into your Dukaan merchant account to access revenue analytics and store controls.
        </p>
        <a
          href="/login"
          className="inline-flex items-center gap-2 px-6 py-3 bg-black text-white rounded-2xl font-bold text-sm shadow-md hover:bg-stone-800 transition"
        >
          Proceed to Login <ArrowRight size={16} />
        </a>
      </div>
    );
  }

  // Security check for Merchant role
  if (user?.role !== "merchant") {
    return (
      <div className="max-w-md mx-auto my-24 p-8 text-center bg-white rounded-3xl border border-stone-200 shadow-xl">
        <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <ShieldCheck size={28} />
        </div>
        <h2 className="text-2xl font-black text-stone-900 mb-2">Merchant Access Restricted</h2>
        <p className="text-sm text-stone-500 mb-4">
          This portal is reserved for Dukaan merchant store administrators.
        </p>
        <div className="bg-stone-50 p-3 rounded-xl border border-stone-100 text-xs text-stone-600 font-mono mb-6">
          Current Role: <span className="font-bold text-stone-900">{user?.role || "customer"}</span>
        </div>
        <a
          href="/"
          className="inline-flex items-center gap-2 px-6 py-2.5 bg-stone-100 text-stone-800 rounded-xl font-bold text-xs hover:bg-stone-200 transition"
        >
          Return to Storefront
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8 space-y-8 animate-fadeIn">
      {/* Top Banner / Merchant Executive Strip */}
      <div className="bg-white rounded-3xl border border-stone-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <span className="bg-black text-white text-[11px] font-black uppercase tracking-wider px-2.5 py-1 rounded-lg">
              Merchant Portal
            </span>
            <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              AI Stylist Live & Haggling Bounds Enforced
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-stone-900 tracking-tight">
            Dukaan Merchant Center
          </h1>
          <p className="text-sm text-stone-500 mt-1">
            Welcome back, <strong className="text-stone-800">{user?.name || "Merchant"}</strong>. Monitor live store revenue, top sellers, and AI negotiation audits.
          </p>
        </div>

        {/* Quick actions strip */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition flex items-center gap-2 ${
              activeTab === "analytics"
                ? "bg-black text-white shadow-md shadow-black/10"
                : "bg-stone-100 text-stone-700 hover:bg-stone-200"
            }`}
          >
            <TrendingUp size={16} /> Revenue & Top Items
          </button>
          <button
            onClick={() => setActiveTab("agent")}
            className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition flex items-center gap-2 ${
              activeTab === "agent"
                ? "bg-orange-600 text-white shadow-md shadow-orange-600/20"
                : "bg-orange-50 text-orange-800 hover:bg-orange-100 border border-orange-200"
            }`}
          >
            <Sparkles size={16} /> AI Co-Pilot
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <MerchantTabs
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        counts={{
          orders: orders.length,
          threads: threads.length,
          logs: logs.length,
        }}
      />

      {/* Tab Content Display */}
      <div>
        {/* ANALYTICS TAB */}
        {activeTab === "analytics" && <MerchantAnalytics />}

        {/* CHAT TRANSCRIPTS TAB */}
        {activeTab === "chats" && <ChatTranscriptsTab threads={threads} loading={loading} />}

        {/* ORDERS TAB */}
        {activeTab === "orders" && <OrdersTab orders={orders} loading={loading} />}

        {/* AUDIT LOGS TAB */}
        {activeTab === "audit" && <AuditLogsTab logs={logs} loading={loading} error={error} />}

        {/* AI CO-PILOT TAB */}
        {activeTab === "agent" && (
          <div className="space-y-4">
            <div className="bg-white p-6 rounded-3xl border border-stone-200 shadow-sm">
              <h2 className="text-xl font-black text-stone-900 tracking-tight">
                Merchant AI Assistant
              </h2>
              <p className="text-xs text-stone-500 mt-1">
                Ask questions about your catalog, revenue velocity, inventory reorders, or customer discounts.
              </p>
            </div>
            <MerchantAgentTab />
          </div>
        )}

        {/* ADD PRODUCT TAB */}
        {activeTab === "add_product" && (
          <div className="max-w-2xl bg-white p-8 rounded-3xl border border-stone-200 shadow-sm">
            <h2 className="text-2xl font-black text-stone-900 mb-2">Publish New Catalog Item</h2>
            <p className="text-xs text-stone-500 mb-6">
              Add a new item to your Dukaan storefront with cost price, profit bounds, and inventory stock.
            </p>
            <MerchantProductForm />
          </div>
        )}
      </div>
    </div>
  );
}
