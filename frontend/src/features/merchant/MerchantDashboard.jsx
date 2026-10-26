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
    <div className="max-w-6xl mx-auto py-5 sm:py-6 px-4 sm:px-6 space-y-4 animate-fadeIn">
      {/* Sleek, Compact Merchant Header */}
      <div className="flex items-center justify-between pb-1">
        <div className="flex items-center gap-2.5">
          <h1 className="text-lg sm:text-xl font-bold tracking-tight text-stone-900">
            Merchant Center
          </h1>
          <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            AI Stylist Active
          </span>
        </div>
        <p className="hidden sm:block text-xs text-stone-400">
          Welcome back, <strong className="text-stone-700 font-semibold">{user?.name || "Merchant"}</strong>
        </p>
      </div>

      {/* Tab Navigation */}
      <MerchantTabs
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        counts={{
          orders: orders?.length,
          threads: threads?.length,
          logs: logs?.length,
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
