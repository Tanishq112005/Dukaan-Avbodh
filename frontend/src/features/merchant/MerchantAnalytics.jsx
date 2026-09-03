import { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export function MerchantAnalytics() {
  const { token } = useStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;

    const fetchAnalytics = async () => {
      try {
        const res = await axios.get(
          `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/analytics`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        setData(res.data);
      } catch (err) {
        setError("Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [token]);

  if (loading) return <p>Loading analytics...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!data) return null;

  const { metrics, revenue_by_category, revenue_trend } = data;

  return (
    <div className="space-y-8">
      {/* Top Level Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-semibold text-gray-500 uppercase">
            Total Revenue
          </p>
          <p className="text-3xl font-black mt-2 text-green-600">
            ₹{metrics.total_revenue}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-semibold text-gray-500 uppercase">
            Total Profit
          </p>
          <p className="text-3xl font-black mt-2">₹{metrics.total_profit}</p>
          <p className="text-xs text-gray-400 mt-1">
            Margin: {metrics.profit_margin_percent}%
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-semibold text-gray-500 uppercase">
            Total Orders
          </p>
          <p className="text-3xl font-black mt-2">{metrics.total_orders}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Orders Per Day Chart */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-bold mb-4">Orders Placed Per Day</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenue_trend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" />
                <YAxis allowDecimals={false} />
                <RechartsTooltip />
                <Legend />
                <Bar
                  dataKey="orders"
                  fill="#16a34a"
                  name="Orders"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Chart */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-bold mb-4">Performance by Category</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revenue_by_category}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Bar
                  dataKey="revenue"
                  fill="#000000"
                  name="Revenue (₹)"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="profit"
                  fill="#16a34a"
                  name="Profit (₹)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
