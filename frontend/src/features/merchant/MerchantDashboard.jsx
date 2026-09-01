import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [logs, setLogs] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
      
      <div className="grid md:grid-cols-2 gap-12 mb-12">
        <div>
          <h2 className="text-2xl font-bold mb-6">Add New Product</h2>
          <MerchantProductForm />
        </div>

        <div>
          <h2 className="text-2xl font-bold mb-6">Security & Audit Logs</h2>
          <p className="text-sm text-gray-500 mb-4">
            Transparent logs of all AI negotiations, profit margins, and strict bounds enforcement.
          </p>
          
          {loading ? (
            <p>Loading logs...</p>
          ) : error ? (
            <p className="text-red-500">{error}</p>
          ) : logs.length === 0 ? (
            <p className="text-gray-400">No audit logs found yet.</p>
          ) : (
            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
              {logs.map((log) => (
                <div key={log._id} className="bg-gray-100 p-4 rounded-lg text-sm border-l-4 border-black">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-black uppercase tracking-wider">{log.action}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-2">
                    <strong>Reasoning:</strong> {log.reason}
                  </p>
                  <p className="text-green-700 font-semibold mb-2">
                    <strong>Result:</strong> {log.result}
                  </p>
                  
                  {log.metadata?.products && log.metadata.products.length > 0 && (
                    <div className="mt-3 bg-white p-3 rounded border border-gray-200">
                      <p className="text-xs font-bold text-gray-500 uppercase mb-2">Products in Discussion</p>
                      <div className="flex flex-col gap-2">
                        {log.metadata.products.map((p, idx) => (
                          <div key={idx} className="flex items-center gap-3">
                            <img src={p.image_url} alt={p.name} className="w-8 h-8 rounded object-cover border" />
                            <div>
                              <p className="text-xs font-semibold line-clamp-1">{p.name}</p>
                              <p className="text-xs text-gray-500">₹{p.price}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {log.user_id && (
                    <p className="text-xs text-gray-500 mt-3">User ID: {log.user_id}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

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
                
                <hr className="my-4" />
                
                <div className="space-y-2 text-sm text-gray-600">
                  <p><strong className="text-black">Customer:</strong> {order.user.name}</p>
                  <p><strong className="text-black">Email:</strong> {order.user.email}</p>
                  <p><strong className="text-black">Delivery To:</strong> {order.user.address}</p>
                </div>
                
                <hr className="my-4" />
                
                <div className="space-y-1 text-xs text-gray-500">
                  <p>Order ID: {order.id}</p>
                  <p>Razorpay Order: {order.razorpay_order_id || "N/A"}</p>
                  <p>Razorpay Payment: {order.razorpay_payment_id || "N/A"}</p>
                  <p>Date: {new Date(order.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
