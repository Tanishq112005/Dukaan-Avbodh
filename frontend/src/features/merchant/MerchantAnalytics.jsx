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
    <div className="space-y-4 animate-fadeIn">
      {/* Top Bar: Time Range Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900 text-white p-3 sm:px-4 sm:py-2.5 rounded-2xl shadow-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <div>
            <h3 className="text-sm font-bold tracking-tight text-white">Executive Performance Hub</h3>
            <p className="text-[10px] text-stone-400">
              Real-time multi-channel revenue, margins, and catalog velocity
            </p>
          </div>
        </div>

        {/* Time filters */}
        <div className="flex items-center bg-stone-800/90 p-1 rounded-xl border border-stone-700/60 self-start sm:self-auto">
          {timeRanges.map((tr) => (
            <button
              key={tr.id}
              onClick={() => setTimeRange(tr.id)}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all cursor-pointer ${
                timeRange === tr.id
                  ? "bg-white text-stone-900 shadow-xs font-bold"
                  : "text-stone-300 hover:text-white hover:bg-stone-700/50"
              }`}
            >
              {tr.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Total Revenue */}
        <div className="bg-white p-3.5 sm:p-4 rounded-2xl border border-stone-200/80 shadow-xs hover:shadow-sm transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold tracking-wider uppercase text-stone-400">
              Gross Revenue
            </span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <DollarSign size={15} />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-black text-stone-900 font-mono tracking-tight">
              ₹{Number(metrics.total_revenue || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px]">
            <span className="inline-flex items-center text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded-md">
              <ArrowUpRight size={12} className="mr-0.5" /> +14.8%
            </span>
            <span className="text-stone-400">vs prev cycle</span>
          </div>
        </div>

        {/* Total Net Profit */}
        <div className="bg-white p-3.5 sm:p-4 rounded-2xl border border-stone-200/80 shadow-xs hover:shadow-sm transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold tracking-wider uppercase text-stone-400">
              Net Profit
            </span>
            <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <TrendingUp size={15} />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-black text-stone-900 font-mono tracking-tight">
              ₹{Number(metrics.total_profit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px]">
            <span className="inline-flex items-center text-blue-700 font-bold bg-blue-50 px-1.5 py-0.5 rounded-md">
              {metrics.profit_margin_percent || 0}% Margin
            </span>
            <span className="text-stone-400">healthy return</span>
          </div>
        </div>

        {/* Total Orders & Volume */}
        <div className="bg-white p-3.5 sm:p-4 rounded-2xl border border-stone-200/80 shadow-xs hover:shadow-sm transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold tracking-wider uppercase text-stone-400">
              Total Orders
            </span>
            <div className="w-7 h-7 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center">
              <ShoppingBag size={15} />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-black text-stone-900 tracking-tight font-mono">
              {metrics.total_orders || 0}
            </span>
            <span className="text-xs font-semibold text-stone-500">
              ({metrics.total_items_sold || 0} items)
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px]">
            <span className="text-stone-500 font-medium">AOV:</span>
            <span className="font-bold text-stone-900 font-mono">
              ₹{Number(metrics.average_order_value || 0).toFixed(0)}
            </span>
            <span className="text-stone-400">/ order</span>
          </div>
        </div>

        {/* AI Negotiated Discounts */}
        <div className="bg-white p-3.5 sm:p-4 rounded-2xl border border-stone-200/80 shadow-xs hover:shadow-sm transition-shadow relative overflow-hidden group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold tracking-wider uppercase text-stone-400">
              AI Discounts Given
            </span>
            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Percent size={15} />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-black text-purple-900 font-mono tracking-tight">
              ₹{Number(metrics.total_ai_discount_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-[11px]">
            <span className="inline-flex items-center text-purple-700 font-bold bg-purple-50 px-1.5 py-0.5 rounded-md">
              Avg {metrics.average_discount_percent || 0}%
            </span>
            <span className="text-stone-400">bounded within cap</span>
          </div>
        </div>
      </div>

      {/* SECTION: Which Item is Selling More (Top Selling Products) */}
      <div className="bg-white rounded-2xl border border-stone-200/80 shadow-xs overflow-hidden p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-100">
          <div>
            <div className="flex items-center gap-2">
              <Flame className="text-[#C45C26]" size={18} />
              <h3 className="text-base font-bold text-stone-900 tracking-tight">
                Top-Selling Products
              </h3>
              <span className="bg-orange-100/70 text-orange-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                {topSelling.length} active items
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-0.5">
              Live inventory velocity, unit demand, and profit generated per product
            </p>
          </div>

          {/* Sort controls */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-stone-400 font-medium text-[11px]">Sort:</span>
            <div className="inline-flex bg-stone-100 p-0.5 rounded-lg border border-stone-200/60">
              <button
                onClick={() => setSortBy("units_sold")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition cursor-pointer ${
                  sortBy === "units_sold" ? "bg-white text-stone-900 shadow-xs font-bold" : "text-stone-500 hover:text-stone-900"
                }`}
              >
                Units Sold
              </button>
              <button
                onClick={() => setSortBy("revenue")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition cursor-pointer ${
                  sortBy === "revenue" ? "bg-white text-stone-900 shadow-xs font-bold" : "text-stone-500 hover:text-stone-900"
                }`}
              >
                Revenue
              </button>
              <button
                onClick={() => setSortBy("profit")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition cursor-pointer ${
                  sortBy === "profit" ? "bg-white text-stone-900 shadow-xs font-bold" : "text-stone-500 hover:text-stone-900"
                }`}
              >
                Profit
              </button>
            </div>
          </div>
        </div>

        {/* Product Leaderboard Table */}
        {topSelling.length === 0 ? (
          <div className="py-8 text-center text-stone-400 text-xs">
            No sales data available for this timeframe.
          </div>
        ) : (
          <div className="overflow-x-auto mt-2 custom-scrollbar">
            <table className="w-full text-left text-xs border-collapse min-w-[650px]">
              <thead>
                <tr className="border-b border-stone-100 text-[10px] font-bold uppercase tracking-wider text-stone-400">
                  <th className="py-2.5 px-3 w-10 text-center">Rank</th>
                  <th className="py-2.5 px-3">Product Details</th>
                  <th className="py-2.5 px-3 text-center">Units Sold</th>
                  <th className="py-2.5 px-3 text-right">Revenue</th>
                  <th className="py-2.5 px-3 text-right">Profit</th>
                  <th className="py-2.5 px-3 text-center">Stock</th>
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
                      <td className="py-2.5 px-3 text-center">
                        {idx === 0 ? (
                          <span className="w-5 h-5 rounded-full bg-amber-400 text-stone-900 font-bold text-[10px] inline-flex items-center justify-center shadow-xs">
                            1
                          </span>
                        ) : idx === 1 ? (
                          <span className="w-5 h-5 rounded-full bg-stone-300 text-stone-900 font-bold text-[10px] inline-flex items-center justify-center shadow-xs">
                            2
                          </span>
                        ) : idx === 2 ? (
                          <span className="w-5 h-5 rounded-full bg-amber-600/30 text-amber-900 font-bold text-[10px] inline-flex items-center justify-center shadow-xs">
                            3
                          </span>
                        ) : (
                          <span className="text-stone-400 font-mono text-[11px]">
                            #{idx + 1}
                          </span>
                        )}
                      </td>

                      {/* Product Thumbnail & Title */}
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-9 h-11 bg-stone-100 rounded-lg overflow-hidden shrink-0 border border-stone-200/80">
                            {prod.image_url ? (
                              <img
                                src={prod.image_url}
                                alt={prod.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-stone-300">
                                <Package size={14} />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-semibold text-stone-900 line-clamp-1 group-hover:text-[#6e1423] transition-colors text-xs">
                              {prod.name}
                            </p>
                            <span className="text-[10px] text-stone-400 uppercase tracking-wider font-semibold">
                              {prod.category || "Apparel"}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Units Sold with Progress Bar */}
                      <td className="py-2.5 px-3 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className="font-bold text-xs text-stone-900 font-mono">
                            {prod.units_sold} pcs
                          </span>
                          <div className="w-16 bg-stone-100 rounded-full h-1 mt-1 overflow-hidden">
                            <div
                              className="bg-[#C45C26] h-full rounded-full transition-all duration-500"
                              style={{ width: `${Math.max(10, unitPct)}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Revenue */}
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-stone-900 text-xs">
                        ₹{Number(prod.total_revenue || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>

                      {/* Profit */}
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-emerald-700 text-xs">
                        +₹{Number(prod.total_profit || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>

                      {/* Current Stock */}
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            prod.stock_remaining < 5
                              ? "bg-red-50 text-red-700 border border-red-200/60"
                              : prod.stock_remaining < 15
                              ? "bg-amber-50 text-amber-700 border border-amber-200/60"
                              : "bg-stone-100 text-stone-700"
                          }`}
                        >
                          {prod.stock_remaining} left
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Daily Sales & Revenue Trend Chart */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-stone-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-sm font-bold text-stone-900 tracking-tight">
                Daily Revenue & Sales Trend
              </h3>
              <p className="text-[11px] text-stone-400 mt-0.5">
                Timeline of revenue generated vs AI discounts granted
              </p>
            </div>
            <span className="p-1.5 rounded-lg bg-stone-100 text-stone-600">
              <TrendingUp size={15} />
            </span>
          </div>

          <div className="h-60 w-full mt-2">
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
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#a8a29e" />
                <YAxis tick={{ fontSize: 10 }} stroke="#a8a29e" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e7e5e4",
                    boxShadow: "0 6px 12px -2px rgba(0, 0, 0, 0.08)",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#revenueGrad)"
                  name="Revenue (₹)"
                />
                <Area
                  type="monotone"
                  dataKey="profit"
                  stroke="#000000"
                  strokeWidth={1.5}
                  fillOpacity={1}
                  fill="url(#profitGrad)"
                  name="Net Profit (₹)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Performance Breakdown Chart */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-stone-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-sm font-bold text-stone-900 tracking-tight">
                Category Performance
              </h3>
              <p className="text-[11px] text-stone-400 mt-0.5">
                Relative profitability and unit volume by category
              </p>
            </div>
            <span className="p-1.5 rounded-lg bg-stone-100 text-stone-600">
              <Layers size={15} />
            </span>
          </div>

          <div className="h-60 w-full mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0ede6" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#a8a29e" />
                <YAxis tick={{ fontSize: 10 }} stroke="#a8a29e" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    borderRadius: "12px",
                    border: "1px solid #e7e5e4",
                    boxShadow: "0 6px 12px -2px rgba(0, 0, 0, 0.08)",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Bar dataKey="revenue" fill="#1c1917" name="Revenue (₹)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="profit" fill="#f97316" name="Profit (₹)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION: AI Negotiation Funnel & Conversion Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 bg-gradient-to-br from-stone-900 to-stone-850 text-white p-4 sm:p-5 rounded-2xl shadow-xs">
          <div className="flex items-center gap-2.5 mb-3.5">
            <div className="w-7 h-7 rounded-lg bg-orange-500/20 text-orange-400 flex items-center justify-center">
              <Sparkles size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Haggling & Conversion Intelligence</h3>
              <p className="text-[10px] text-stone-400">
                Audited metrics from customer negotiations and automated profit bounds
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
              <p className="text-[10px] text-stone-400 uppercase font-semibold">Total Sessions</p>
              <p className="text-lg sm:text-xl font-black text-white mt-0.5 font-mono">
                {negotiation.total_chat_sessions || 0}
              </p>
              <p className="text-[10px] text-stone-400 mt-0.5">all customers</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
              <p className="text-[10px] text-stone-400 uppercase font-semibold">Haggling Rounds</p>
              <p className="text-lg sm:text-xl font-black text-amber-400 mt-0.5 font-mono">
                {negotiation.total_negotiation_rounds || 0}
              </p>
              <p className="text-[10px] text-stone-400 mt-0.5">counter-offers made</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
              <p className="text-[10px] text-stone-400 uppercase font-semibold">Avg Ask / Given</p>
              <p className="text-base sm:text-lg font-black text-white mt-0.5 font-mono">
                {negotiation.average_discount_requested || 0}% / <span className="text-emerald-400">{negotiation.average_discount_granted || 0}%</span>
              </p>
              <p className="text-[10px] text-stone-400 mt-0.5">margin protected</p>
            </div>

            <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
              <p className="text-[10px] text-stone-400 uppercase font-semibold">Chat Conversion</p>
              <p className="text-lg sm:text-xl font-black text-emerald-400 mt-0.5 font-mono">
                {negotiation.conversion_rate || 0}%
              </p>
              <p className="text-[10px] text-stone-400 mt-0.5">
                {negotiation.orders_placed_from_chat || 0} orders closed
              </p>
            </div>
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-stone-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="text-amber-500" size={16} />
                <h3 className="font-bold text-xs sm:text-sm text-stone-900">Restock Alerts</h3>
              </div>
              <span className="text-[10px] font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded-full border border-amber-200/60">
                {alerts.length} items
              </span>
            </div>
            <p className="text-[11px] text-stone-500 mb-3">
              Catalog items with stock under 10 units
            </p>

            {alerts.length === 0 ? (
              <div className="py-6 text-center text-stone-400 text-xs">
                <CheckCircle2 size={22} className="mx-auto mb-1 text-emerald-500" />
                All catalog inventory levels healthy.
              </div>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-1">
                {alerts.slice(0, 4).map((al) => (
                  <div
                    key={al.product_id}
                    className="flex items-center justify-between p-2 rounded-lg border border-stone-100 bg-stone-50"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-md overflow-hidden bg-white border border-stone-200/60 shrink-0">
                        {al.image_url ? (
                          <img src={al.image_url} alt={al.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-stone-200" />
                        )}
                      </div>
                      <div className="overflow-hidden">
                        <p className="text-xs font-semibold text-stone-800 truncate max-w-[120px]">
                          {al.name}
                        </p>
                        <p className="text-[10px] text-stone-400 font-mono">₹{al.price}</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100/70 px-2 py-0.5 rounded-md shrink-0">
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
