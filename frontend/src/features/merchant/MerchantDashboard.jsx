import React, { useState } from "react";
import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";
import { MerchantAnalytics } from "./MerchantAnalytics";
import { MerchantTabs } from "./MerchantTabs";
import { AuditLogsTab } from "./AuditLogsTab";
import { OrdersTab } from "./OrdersTab";
import { ChatTranscriptsTab } from "./ChatTranscriptsTab";
import { useMerchantData } from "./useMerchantData";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [activeTab, setActiveTab] = useState("audit");
  const { logs, orders, threads, loading, error } = useMerchantData();

  if (!token) {
    return <div className="p-16 text-center text-red-500 font-bold">Please login first!</div>;
  }

  // Very basic security check for UI (API will still enforce it securely)
  if (user?.role !== "merchant") {
    return (
      <div className="p-16 text-center">
        <h2 className="text-2xl font-bold text-red-500 mb-4">Access Denied</h2>
        <p>Sorry You cannot access this webpage , this webpage is only for the Merchant</p>
        <p className="text-sm text-gray-400 mt-2">Current Role: {user?.role}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-8">Merchant Dashboard</h1>
      
      {/* Tab Navigation */}
      <MerchantTabs activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Tab Content */}
      <div className="mt-8">
        
        {/* ANALYTICS TAB */}
        {activeTab === "analytics" && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Analytics & Revenue</h2>
            <MerchantAnalytics />
          </div>
        )}

        {/* CHATS TAB */}
        {activeTab === "chats" && <ChatTranscriptsTab threads={threads} loading={loading} />}

        {/* ADD PRODUCT TAB */}
        {activeTab === "add_product" && (
          <div className="max-w-xl">
            <h2 className="text-2xl font-bold mb-6">Add New Product</h2>
            <MerchantProductForm />
          </div>
        )}

        {/* AUDIT LOGS TAB */}
        {activeTab === "audit" && <AuditLogsTab logs={logs} loading={loading} error={error} />}

        {/* ORDERS TAB */}
        {activeTab === "orders" && <OrdersTab orders={orders} loading={loading} />}
        
      </div>
    </div>
  );
}
