import React from "react";
import {
  BarChart3,
  MessageSquare,
  ShoppingBag,
  ShieldCheck,
  Sparkles,
  PlusCircle,
} from "lucide-react";

export function MerchantTabs({ activeTab, setActiveTab, counts = {} }) {
  const tabs = [
    {
      id: "analytics",
      label: "Analytics & Revenue",
      icon: BarChart3,
      badge: counts.revenue ? `₹${counts.revenue}` : null,
      badgeColor: "bg-emerald-100 text-emerald-800",
    },
    {
      id: "chats",
      label: "Customer Chats",
      icon: MessageSquare,
      badge: counts.threads ? counts.threads : null,
      badgeColor: "bg-blue-100 text-blue-800",
    },
    {
      id: "orders",
      label: "Live Orders",
      icon: ShoppingBag,
      badge: counts.orders ? counts.orders : null,
      badgeColor: "bg-orange-100 text-orange-800",
    },
    {
      id: "audit",
      label: "Security & Audits",
      icon: ShieldCheck,
      badge: counts.logs ? counts.logs : null,
      badgeColor: "bg-purple-100 text-purple-800",
    },
    {
      id: "agent",
      label: "AI Co-Pilot",
      icon: Sparkles,
      badge: "PRO",
      badgeColor: "bg-amber-100 text-amber-800 font-bold text-[10px]",
    },
    {
      id: "add_product",
      label: "Add Product",
      icon: PlusCircle,
    },
  ];

  return (
    <div className="w-full bg-white rounded-2xl border border-stone-200 p-1.5 shadow-sm mb-8 overflow-x-auto custom-scrollbar">
      <div className="flex items-center gap-1.5 min-w-max">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200 whitespace-nowrap ${
                isActive
                  ? "bg-black text-white shadow-md shadow-black/10 scale-[1.01]"
                  : "text-stone-600 hover:text-black hover:bg-stone-100/80"
              }`}
            >
              <Icon
                size={17}
                className={isActive ? "text-orange-400" : "text-stone-400"}
              />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    isActive ? "bg-white/20 text-white" : tab.badgeColor
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
