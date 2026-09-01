import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { MerchantProductForm } from "./MerchantProductForm";

export function MerchantDashboard() {
  const { token, user } = useStore();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;

    const fetchLogs = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/audit-logs`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setLogs(res.data.logs || []);
      } catch (err) {
        console.error("Failed to fetch audit logs", err);
        setError("Could not load audit logs. Are you a merchant?");
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
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
      
      <div className="grid md:grid-cols-2 gap-12">
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
                  <p className="text-green-700 font-semibold">
                    <strong>Result:</strong> {log.result}
                  </p>
                  {log.user_id && (
                    <p className="text-xs text-gray-500 mt-2">User ID: {log.user_id}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
