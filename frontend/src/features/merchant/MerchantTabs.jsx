export function MerchantTabs({ activeTab, setActiveTab }) {
  const tabs = [
    { id: "audit", label: "Security & Audit Logs" },
    { id: "chats", label: "Chat Transcripts" },
    { id: "analytics", label: "Analytics & Revenue" },
    { id: "orders", label: "Recent Orders" },
    { id: "add_product", label: "Add New Product" },
  ];
  return (
    <div className="flex border-b border-gray-200 mb-8 overflow-x-auto">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`py-3 px-6 font-semibold whitespace-nowrap transition-colors ${
            activeTab === tab.id ? "border-b-2 border-black text-black" : "text-gray-500 hover:text-black"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
