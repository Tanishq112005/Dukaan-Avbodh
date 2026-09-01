import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";
import { MerchantAnalytics } from "./MerchantAnalytics";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [logs, setLogs] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [activeTab, setActiveTab] = useState("audit");

  useEffect(() => {
    if (!token) return;

    const fetchDashboardData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [logsRes, ordersRes] = await Promise.all([
          axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/audit-logs`, { headers }),
          axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/orders`, { headers })
        ]);
        
        setLogs(logsRes.data.logs || []);
        setOrders(ordersRes.data.orders || []);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
        setError("Could not load dashboard data. Are you a merchant?");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [token]);

  if (!token) {
    return <div className="p-16 text-center text-red-500 font-bold">Please login first!</div>;
  }

  // Very basic security check for UI (API will still enforce it securely)
  if (user?.role !== "merchant") {
    return (
      <div className="p-16 text-center">
        <h2 className="text-2xl font-bold text-red-500 mb-4">Access Denied</h2>
        <p>You must be a Merchant to view this page.</p>
        <p className="text-sm text-gray-400 mt-2">Current Role: {user?.role}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-16 px-4">
      <h1 className="text-4xl font-black mb-8">Merchant Dashboard</h1>
      
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-8 overflow-x-auto">
        <button
          onClick={() => setActiveTab("audit")}
          className={`py-3 px-6 font-semibold whitespace-nowrap transition-colors ${
            activeTab === "audit" 
              ? "border-b-2 border-black text-black" 
              : "text-gray-500 hover:text-black"
          }`}
        >
          Security & Audit Logs
        </button>
        <button
          onClick={() => setActiveTab("analytics")}
          className={`py-3 px-6 font-semibold whitespace-nowrap transition-colors ${
            activeTab === "analytics" 
              ? "border-b-2 border-black text-black" 
              : "text-gray-500 hover:text-black"
          }`}
        >
          Analytics & Revenue
        </button>
        <button
          onClick={() => setActiveTab("orders")}
          className={`py-3 px-6 font-semibold whitespace-nowrap transition-colors ${
            activeTab === "orders" 
              ? "border-b-2 border-black text-black" 
              : "text-gray-500 hover:text-black"
          }`}
        >
          Recent Orders
        </button>
        <button
          onClick={() => setActiveTab("add_product")}
          className={`py-3 px-6 font-semibold whitespace-nowrap transition-colors ${
            activeTab === "add_product" 
              ? "border-b-2 border-black text-black" 
              : "text-gray-500 hover:text-black"
          }`}
        >
          Add New Product
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-8">
        
        {/* ANALYTICS TAB */}
        {activeTab === "analytics" && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Analytics & Revenue</h2>
            <MerchantAnalytics />
          </div>
        )}

        {/* ADD PRODUCT TAB */}
        {activeTab === "add_product" && (
          <div className="max-w-xl">
            <h2 className="text-2xl font-bold mb-6">Add New Product</h2>
            <MerchantProductForm />
          </div>
        )}

        {/* AUDIT LOGS TAB */}
        {activeTab === "audit" && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold mb-2">Security & Audit Logs</h2>
                <p className="text-sm text-gray-500">
                  Transparent logs of all AI negotiations, profit margins, and strict bounds enforcement.
                </p>
              </div>
            </div>
            
            {loading ? (
              <p>Loading logs...</p>
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : logs.length === 0 ? (
              <p className="text-gray-400">No audit logs found yet.</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {logs.map((log) => (
                  <div key={log._id} className="bg-gray-100 p-5 rounded-lg text-sm border-l-4 border-black">
                    <div className="flex justify-between items-start mb-3">
                      <span className="font-bold text-black uppercase tracking-wider bg-white px-2 py-1 rounded text-xs">{log.action}</span>
                      <span className="text-xs text-gray-500 font-medium">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-gray-800 mb-3 bg-white p-3 rounded">
                      <strong>Reasoning:</strong><br />{log.reason}
                    </p>
                    <p className="text-green-700 font-bold mb-2 text-base">
                      {log.result}
                    </p>
                    
                    {log.metadata?.products && log.metadata.products.length > 0 && (
                      <div className="mt-4 bg-white p-3 rounded border border-gray-200">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Products in Discussion</p>
                        <div className="flex flex-col gap-2">
                          {log.metadata.products.map((p, idx) => (
                            <div key={idx} className="flex items-center gap-3">
                              <img src={p.image_url} alt={p.name} className="w-10 h-10 rounded object-cover border" />
                              <div>
                                <p className="text-sm font-semibold line-clamp-1">{p.name}</p>
                                <p className="text-xs text-gray-500">₹{p.price}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {log.user_id && (
                      <p className="text-xs text-gray-400 mt-4 text-right">User ID: {log.user_id}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ORDERS TAB */}
        {activeTab === "orders" && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Recent Orders</h2>
            {loading ? (
              <p>Loading orders...</p>
            ) : orders.length === 0 ? (
              <p className="text-gray-400">No orders placed yet.</p>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {orders.map((order) => (
                  <div key={order.id} className="border border-gray-200 rounded-xl p-6 bg-white shadow-sm hover:shadow-md transition">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                        {order.product.image_url ? (
                          <img src={order.product.image_url} alt={order.product.name} className="w-full h-full object-cover mix-blend-multiply" />
                        ) : (
                          <div className="w-full h-full bg-gray-200"></div>
                        )}
                      </div>
                      <div>
                        <h3 className="font-bold line-clamp-1">{order.product.name}</h3>
                        <p className="text-sm text-gray-500">Price: ₹{order.product.price} (Discount: {order.discount_applied}%)</p>
                      </div>
                    </div>
                    
                    <hr className="my-4 border-gray-100" />
                    
                    <div className="space-y-2 text-sm text-gray-600 bg-gray-50 p-3 rounded">
                      <p><strong className="text-black">Customer:</strong> {order.user.name}</p>
                      <p><strong className="text-black">Email:</strong> {order.user.email}</p>
                      <p><strong className="text-black">Delivery To:</strong> {order.user.address}</p>
                    </div>
                    
                    <hr className="my-4 border-gray-100" />
                    
                    <div className="space-y-1 text-xs text-gray-400">
                      <p>Order ID: #{order.id}</p>
                      <p>Razorpay Order: {order.razorpay_order_id || "N/A"}</p>
                      <p>Razorpay Payment: {order.razorpay_payment_id || "N/A"}</p>
                      <p>Date: {new Date(order.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
      </div>
    </div>
  );
}
