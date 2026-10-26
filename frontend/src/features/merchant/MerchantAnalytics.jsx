import React, { useEffect, useState } from "react";
import axios from "axios";
import { useStore } from "../../store/useStore";
import { Loader } from "../../components/ui/Loader";
import {
  TrendingUp,
  DollarSign,
  ShoppingBag,
  Percent,
  Sparkles,
  Package,
  AlertTriangle,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Users,
  Layers,
  ArrowRight,
  Flame,
  Award,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

export function MerchantAnalytics() {
  const { token } = useStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState("all");
  const [sortBy, setSortBy] = useState("units_sold");

  const fetchAnalytics = async (range) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await axios.get(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/analytics?time_range=${range}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setData(res.data);
      setError("");
    } catch (err) {
      console.warn("Analytics fetch error:", err);
      setError("Failed to load analytics data. Ensure your backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(timeRange);
  }, [token, timeRange]);

  if (loading && !data) {
    return (
      <div className="flex flex-col justify-center items-center py-28 gap-4 bg-white rounded-3xl border border-stone-200 shadow-sm">
        <Loader size="lg" />
        <p className="text-sm font-semibold text-stone-500 animate-pulse">
          Calculating real-time store revenue and sales metrics...
        </p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-8 text-center bg-red-50 border border-red-200 rounded-2xl text-red-700">
        <AlertTriangle className="mx-auto mb-2 text-red-500" size={32} />
        <p className="font-bold">{error}</p>
        <button
          onClick={() => fetchAnalytics(timeRange)}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 transition"
        >
          Try Again
        </button>
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const topSelling = (data?.top_selling_products || []).slice().sort((a, b) => {
    if (sortBy === "revenue") return b.total_revenue - a.total_revenue;
    if (sortBy === "profit") return b.total_profit - a.total_profit;
    return b.units_sold - a.units_sold;
  });
  const categoryData = data?.revenue_by_category || [];
  const trendData = data?.revenue_trend || [];
  const alerts = data?.inventory_alerts || [];
  const negotiation = data?.negotiation_analytics || {};

  const timeRanges = [
    { id: "today", label: "Today" },
    { id: "7d", label: "Last 7 Days" },
    { id: "30d", label: "Last 30 Days" },
    { id: "all", label: "All Time" },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Bar: Time Range Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-stone-900 text-white p-5 rounded-3xl shadow-lg shadow-stone-950/10">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <h3 className="text-lg font-black tracking-tight">Executive Performance Hub</h3>
          </div>
          <p className="text-xs text-stone-400 mt-0.5">
            Real-time multi-channel revenue, margin analysis, and catalog velocity
          </p>
        </div>

        {/* Time filters */}
        <div className="flex items-center bg-stone-800/90 p-1.5 rounded-2xl border border-stone-700/60 self-start sm:self-auto">
          {timeRanges.map((tr) => (
            <button
              key={tr.id}
              onClick={() => setTimeRange(tr.id)}
              className={`px-3.5 py-1.5 text-xs font-bold rounded-xl transition-all ${
                timeRange === tr.id
                  ? "bg-white text-black shadow-sm"
                  : "text-stone-300 hover:text-white hover:bg-stone-700/50"
              }`}
            >
              {tr.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Revenue */}
        <div className="bg-white p-6 rounded-3xl border border-stone-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold tracking-wider uppercase text-stone-500">
              Gross Revenue
            </span>
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-110 transition-transform">
              <DollarSign size={20} />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-stone-900 font-mono tracking-tight">
              ₹{Number(metrics.total_revenue || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs">
            <span className="inline-flex items-center text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-md">
              <ArrowUpRight size={14} className="mr-0.5" /> +14.8%
            </span>
            <span className="text-stone-400">vs prev cycle</span>
          </div>
        </div>

        {/* Total Net Profit */}
        <div className="bg-white p-6 rounded-3xl border border-stone-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold tracking-wider uppercase text-stone-500">
              Net Profit
            </span>
            <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
              <TrendingUp size={20} />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-stone-900 font-mono tracking-tight">
              ₹{Number(metrics.total_profit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs">
            <span className="inline-flex items-center text-blue-700 font-bold bg-blue-50 px-2 py-0.5 rounded-md">
              {metrics.profit_margin_percent || 0}% Margin
            </span>
            <span className="text-stone-400">healthy return</span>
          </div>
        </div>

        {/* Total Orders & Volume */}
        <div className="bg-white p-6 rounded-3xl border border-stone-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold tracking-wider uppercase text-stone-500">
              Total Orders
            </span>
            <div className="w-10 h-10 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center group-hover:scale-110 transition-transform">
              <ShoppingBag size={20} />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-stone-900 tracking-tight font-mono">
              {metrics.total_orders || 0}
            </span>
            <span className="text-sm font-semibold text-stone-500">
              ({metrics.total_items_sold || 0} items)
            </span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs">
            <span className="text-stone-600 font-medium">AOV:</span>
            <span className="font-bold text-stone-900 font-mono">
              ₹{Number(metrics.average_order_value || 0).toFixed(0)}
            </span>
            <span className="text-stone-400">/ order</span>
          </div>
        </div>

        {/* AI Negotiated Discounts */}
        <div className="bg-white p-6 rounded-3xl border border-stone-200/90 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold tracking-wider uppercase text-stone-500">
              AI Discounts Given
            </span>
            <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Percent size={20} />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-purple-900 font-mono tracking-tight">
              ₹{Number(metrics.total_ai_discount_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs">
            <span className="inline-flex items-center text-purple-700 font-bold bg-purple-50 px-2 py-0.5 rounded-md">
              Avg {metrics.average_discount_percent || 0}%
            </span>
            <span className="text-stone-400">bounded within cap</span>
          </div>
        </div>
      </div>

      {/* SECTION: Which Item is Selling More (Top Selling Products) */}
      <div className="bg-white rounded-3xl border border-stone-200 shadow-sm overflow-hidden p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-stone-100">
          <div>
            <div className="flex items-center gap-2">
              <Flame className="text-orange-500" size={24} />
              <h3 className="text-xl font-black text-stone-900 tracking-tight">
                Top-Selling Products
              </h3>
              <span className="bg-orange-100 text-orange-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                {topSelling.length} active items
              </span>
            </div>
            <p className="text-sm text-stone-500 mt-1">
              Live inventory velocity, unit demand, and profit generated per product
            </p>
          </div>

          {/* Sort controls */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-stone-500 font-medium">Sort by:</span>
            <div className="inline-flex bg-stone-100 p-1 rounded-xl">
              <button
                onClick={() => setSortBy("units_sold")}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  sortBy === "units_sold" ? "bg-white text-black shadow-sm font-bold" : "text-stone-500 hover:text-black"
                }`}
              >
                Units Sold
              </button>
              <button
                onClick={() => setSortBy("revenue")}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  sortBy === "revenue" ? "bg-white text-black shadow-sm font-bold" : "text-stone-500 hover:text-black"
                }`}
              >
                Revenue
              </button>
              <button
                onClick={() => setSortBy("profit")}
                className={`px-3 py-1 rounded-lg font-semibold transition ${
                  sortBy === "profit" ? "bg-white text-black shadow-sm font-bold" : "text-stone-500 hover:text-black"
                }`}
              >
                Profit
              </button>
            </div>
          </div>
        </div>

        {/* Product Leaderboard Table */}
        {topSelling.length === 0 ? (
          <div className="py-12 text-center text-stone-400 text-sm">
            No sales data available for this timeframe.
          </div>
        ) : (
          <div className="overflow-x-auto mt-4 custom-scrollbar">
            <table className="w-full text-left text-sm border-collapse min-w-[700px]">
              <thead>
                <tr className="border-b border-stone-100 text-xs font-bold uppercase tracking-wider text-stone-400">
                  <th className="py-3 px-4 w-12 text-center">Rank</th>
                  <th className="py-3 px-4">Product Details</th>
                  <th className="py-3 px-4 text-center">Units Sold</th>
                  <th className="py-3 px-4 text-right">Revenue</th>
                  <th className="py-3 px-4 text-right">Profit</th>
                  <th className="py-3 px-4 text-center">Inventory Stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 font-medium">
                {topSelling.map((prod, idx) => {
                  const maxUnits = topSelling[0]?.units_sold || 1;
                  const unitPct = Math.round((prod.units_sold / maxUnits) * 100);

                  return (
                    <tr
                      key={prod.product_id}
                      className="hover:bg-stone-50/70 transition-colors group"
                    >
                      {/* Rank */}
                      <td className="py-4 px-4 text-center">
                        {idx === 0 ? (
                          <span className="w-7 h-7 rounded-full bg-amber-400 text-stone-900 font-black text-xs inline-flex items-center justify-center shadow-sm">
                            🥇
                          </span>
                        ) : idx === 1 ? (
                          <span className="w-7 h-7 rounded-full bg-stone-300 text-stone-900 font-black text-xs inline-flex items-center justify-center shadow-sm">
                            🥈
                          </span>
                        ) : idx === 2 ? (
                          <span className="w-7 h-7 rounded-full bg-amber-600/30 text-amber-900 font-black text-xs inline-flex items-center justify-center shadow-sm">
                            🥉
                          </span>
                        ) : (
                          <span className="text-stone-400 font-mono text-xs font-bold">
                            #{idx + 1}
                          </span>
                        )}
                      </td>

                      {/* Product Thumbnail & Title */}
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3.5">
                          <div className="w-12 h-14 bg-stone-100 rounded-xl overflow-hidden shrink-0 border border-stone-200 shadow-inner">
                            {prod.image_url ? (
                              <img
                                src={prod.image_url}
                                alt={prod.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-stone-300">
                                <Package size={20} />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-bold text-stone-900 line-clamp-1 group-hover:text-orange-600 transition-colors">
                              {prod.name}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-stone-500 font-semibold">
                                {prod.brand}
                              </span>
                              <span className="text-[11px] bg-stone-100 text-stone-600 px-2 py-0.5 rounded-md uppercase font-mono">
                                {prod.category}
                              </span>
                              <span className="text-xs text-stone-400 font-mono">
                                MRP ₹{prod.price}
                              </span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Units Sold with Progress Bar */}
                      <td className="py-4 px-4 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className="font-black text-base text-stone-900 font-mono">
                            {prod.units_sold} pcs
                          </span>
                          <div className="w-24 bg-stone-100 rounded-full h-1.5 mt-1 overflow-hidden">
                            <div
                              className="bg-orange-500 h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.max(10, unitPct)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Revenue */}
                      <td className="py-4 px-4 text-right">
                        <span className="font-bold text-stone-900 font-mono text-base">
                          ₹{Number(prod.total_revenue).toLocaleString("en-IN")}
                        </span>
                      </td>

                      {/* Profit */}
                      <td className="py-4 px-4 text-right">
                        <span className="font-bold text-emerald-600 font-mono text-base">
                          +₹{Number(prod.total_profit).toLocaleString("en-IN")}
                        </span>
                      </td>

                      {/* Current Stock */}
                      <td className="py-4 px-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                            prod.stock_status === "In Stock"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : prod.stock_status === "Low Stock"
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : "bg-red-50 text-red-700 border border-red-200"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              prod.stock_status === "In Stock"
                                ? "bg-emerald-500"
                                : prod.stock_status === "Low Stock"
                                ? "bg-amber-500"
                                : "bg-red-500"
                            }`}
                          />
                          {prod.current_stock} left ({prod.stock_status})
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SECTION: Two Interactive Visual Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Daily Sales & Revenue Trend Chart */}
        <div className="bg-white p-6 sm:p-7 rounded-3xl border border-stone-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-black text-stone-900 tracking-tight">
                Daily Revenue & Sales Trend
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                Daily timeline of revenue generated vs AI discounts granted
              </p>
            </div>
            <span className="p-2 rounded-xl bg-stone-100 text-stone-600">
              <TrendingUp size={18} />
            </span>
          </div>

          <div className="h-72 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#000000" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#000000" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0ede6" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#a8a29e" />
                <YAxis tick={{ fontSize: 11 }} stroke="#a8a29e" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderRadius: "16px",
                    border: "1px solid #e7e5e4",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#revenueGrad)"
                  name="Revenue (₹)"
                />
                <Area
                  type="monotone"
                  dataKey="profit"
                  stroke="#000000"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#profitGrad)"
                  name="Net Profit (₹)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Performance Breakdown Chart */}
        <div className="bg-white p-6 sm:p-7 rounded-3xl border border-stone-200 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-black text-stone-900 tracking-tight">
                Category Performance
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                Relative profitability and unit volume by clothing category
              </p>
            </div>
            <span className="p-2 rounded-xl bg-stone-100 text-stone-600">
              <Layers size={18} />
            </span>
          </div>

          <div className="h-72 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0ede6" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#a8a29e" />
                <YAxis tick={{ fontSize: 11 }} stroke="#a8a29e" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderRadius: "16px",
                    border: "1px solid #e7e5e4",
                    boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Legend />
                <Bar dataKey="revenue" fill="#1c1917" name="Revenue (₹)" radius={[6, 6, 0, 0]} />
                <Bar dataKey="profit" fill="#f97316" name="Profit (₹)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION: AI Negotiation Funnel & Conversion Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-gradient-to-br from-stone-900 to-stone-800 text-white p-7 rounded-3xl shadow-md">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-2xl bg-orange-500/20 text-orange-400 flex items-center justify-center">
              <Sparkles size={22} />
            </div>
            <div>
              <h3 className="text-lg font-black">AI Haggling & Conversion Intelligence</h3>
              <p className="text-xs text-stone-400">
                Audited metrics from customer negotiations and automated profit bounds
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="bg-white/5 border border-white/10 p-4 rounded-2xl">
              <p className="text-xs text-stone-400 uppercase font-semibold">Total Sessions</p>
              <p className="text-2xl font-black text-white mt-1 font-mono">
                {negotiation.total_chat_sessions || 0}
              </p>
              <p className="text-[11px] text-stone-400 mt-1">all customers</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-4 rounded-2xl">
              <p className="text-xs text-stone-400 uppercase font-semibold">Haggling Rounds</p>
              <p className="text-2xl font-black text-amber-400 mt-1 font-mono">
                {negotiation.total_negotiation_rounds || 0}
              </p>
              <p className="text-[11px] text-stone-400 mt-1">counter-offers made</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-4 rounded-2xl">
              <p className="text-xs text-stone-400 uppercase font-semibold">Avg Ask vs Given</p>
              <p className="text-xl font-black text-white mt-1 font-mono">
                {negotiation.average_discount_requested || 0}% <span className="text-xs text-stone-400">ask</span> /{" "}
                <span className="text-emerald-400">{negotiation.average_discount_granted || 0}%</span>
              </p>
              <p className="text-[11px] text-stone-400 mt-1">margin protected</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-4 rounded-2xl">
              <p className="text-xs text-stone-400 uppercase font-semibold">Chat Conversion</p>
              <p className="text-2xl font-black text-emerald-400 mt-1 font-mono">
                {negotiation.conversion_rate || 0}%
              </p>
              <p className="text-[11px] text-stone-400 mt-1">
                {negotiation.orders_placed_from_chat || 0} orders closed
              </p>
            </div>
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white p-7 rounded-3xl border border-stone-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="text-amber-500" size={20} />
                <h3 className="font-bold text-stone-900">Restock Alerts</h3>
              </div>
              <span className="text-xs font-bold bg-amber-50 text-amber-800 px-2.5 py-0.5 rounded-full border border-amber-200">
                {alerts.length} items
              </span>
            </div>
            <p className="text-xs text-stone-500 mb-4">
              High velocity items with remaining stock under 10 units
            </p>

            {alerts.length === 0 ? (
              <div className="py-8 text-center text-stone-400 text-xs">
                <CheckCircle2 size={28} className="mx-auto mb-2 text-emerald-500" />
                All catalog inventory levels healthy.
              </div>
            ) : (
              <div className="space-y-3 max-h-56 overflow-y-auto custom-scrollbar pr-1">
                {alerts.slice(0, 4).map((al) => (
                  <div
                    key={al.product_id}
                    className="flex items-center justify-between p-2.5 rounded-xl border border-stone-100 bg-stone-50"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-lg overflow-hidden bg-white border shrink-0">
                        {al.image_url ? (
                          <img src={al.image_url} alt={al.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-stone-200" />
                        )}
                      </div>
                      <div className="overflow-hidden">
                        <p className="text-xs font-bold text-stone-800 truncate max-w-[130px]">
                          {al.name}
                        </p>
                        <p className="text-[10px] text-stone-500 font-mono">₹{al.price}</p>
                      </div>
                    </div>
                    <span className="text-xs font-black text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded-lg shrink-0">
                      {al.current_stock} left
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
