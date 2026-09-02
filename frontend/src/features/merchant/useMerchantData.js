import { useState, useEffect } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";

export function useMerchantData() {
  const [logs, setLogs] = useState([]);
  const [orders, setOrders] = useState([]);
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token } = useStore();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [logsRes, ordersRes, threadsRes] = await Promise.all([
          axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/audit-logs`, {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/orders`, {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/chat-threads`, {
            headers: { Authorization: `Bearer ${token}` }
          })
        ]);
        setLogs(logsRes.data.logs || []);
        setOrders(ordersRes.data.orders || []);
        setThreads(threadsRes.data.threads || []);
        setError("");
      } catch (err) {
        setError("Failed to fetch merchant data.");
      } finally {
        setLoading(false);
      }
    };
    if (token) fetchData();
  }, [token]);

  return { logs, orders, threads, loading, error };
}
