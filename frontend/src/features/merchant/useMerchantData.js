import { useState, useEffect } from "react";
import apiClient from "../../services/api";
import { useStore } from "../../store/useStore";

export function useMerchantData() {
  const [logs, setLogs] = useState([]);
  const [orders, setOrders] = useState([]);
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token, user } = useStore();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [logsRes, ordersRes, threadsRes] = await Promise.all([
          apiClient.get("/merchant/audit-logs"),
          apiClient.get("/merchant/orders"),
          apiClient.get("/merchant/chat-threads"),
        ]);
        setLogs(logsRes.data.logs || []);
        setOrders(ordersRes.data.orders || []);
        setThreads(threadsRes.data.threads || []);
        setError("");
      } catch (err) {
        console.warn("[MerchantData] Error fetching merchant data:", err);
        setError("Failed to fetch merchant data. Verify you are logged in as a merchant.");
      } finally {
        setLoading(false);
      }
    };

    if (token && user?.role === "merchant") {
      fetchData();
    } else {
      setLoading(false);
    }
  }, [token, user?.role]);

  return { logs, orders, threads, loading, error };
}
