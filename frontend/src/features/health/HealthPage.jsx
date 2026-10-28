import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Server,
  Database,
  Cpu,
  Clock,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
  Layers,
  Zap,
} from "lucide-react";
import { healthService } from "../../services/healthService";

export function HealthPage() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [autoRefreshSec, setAutoRefreshSec] = useState(10);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const fetchHealth = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const data = await healthService.getServerHealth();
      setHealthData(data);
      setError(null);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error("Health check error:", err);
      setError(err?.message || "Failed to reach Dukaan backend server.");
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  useEffect(() => {
    if (!autoRefreshSec || autoRefreshSec <= 0) return;
    const interval = setInterval(() => {
      fetchHealth(false);
    }, autoRefreshSec * 1000);
    return () => clearInterval(interval);
  }, [autoRefreshSec, fetchHealth]);

  const status = (healthData?.status || "unknown").toLowerCase();
  const system = healthData?.system || {};
  const services = healthData?.services || {};

  const getStatusBadge = (s) => {
    switch (s) {
      case "healthy":
      case "ready":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wide">
            <CheckCircle2 size={13} className="text-emerald-600" />
            Healthy
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wide">
            <AlertTriangle size={13} className="text-amber-600" />
            Degraded
          </span>
        );
      case "unhealthy":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 uppercase tracking-wide">
            <XCircle size={13} className="text-rose-600" />
            Unhealthy
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 mb-8 border-b border-stone-200">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-stone-900 text-white rounded-2xl flex items-center justify-center shadow-md">
            <Activity size={24} className="text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-stone-900 tracking-tight">
              Server Health &amp; Diagnostics
            </h1>
            <p className="text-xs md:text-sm text-stone-500">
              Live monitoring of backend services, database clusters, and AI subsystems.
            </p>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-3">
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-xl border border-stone-200 text-xs font-medium text-stone-700 shadow-sm">
            <Clock size={14} className="text-stone-400" />
            <select
              value={autoRefreshSec}
              onChange={(e) => setAutoRefreshSec(Number(e.target.value))}
              className="bg-transparent outline-none cursor-pointer text-stone-800 font-semibold"
            >
              <option value={0}>Auto-refresh: Off</option>
              <option value={5}>Auto-refresh: 5s</option>
              <option value={10}>Auto-refresh: 10s</option>
              <option value={30}>Auto-refresh: 30s</option>
            </select>
          </div>

          <button
            onClick={() => fetchHealth(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-2 px-4 py-2 bg-stone-900 hover:bg-stone-800 text-white rounded-xl text-xs font-bold shadow-sm transition disabled:opacity-60"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>

          <a
            href="http://localhost:8000/health"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-stone-50 text-stone-700 border border-stone-200 rounded-xl text-xs font-bold shadow-sm transition"
            title="Open backend standalone HTML dashboard"
          >
            Backend Dashboard
            <ExternalLink size={13} />
          </a>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <XCircle size={20} className="text-rose-600 shrink-0" />
            <div>
              <p className="font-bold text-sm">Server Communication Error</p>
              <p className="text-xs text-rose-600">{error}</p>
            </div>
          </div>
          <button
            onClick={() => fetchHealth(true)}
            className="px-3 py-1.5 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Status Hero */}
      <div
        className={`p-6 rounded-3xl border shadow-sm mb-6 transition-all ${
          status === "healthy"
            ? "bg-white border-emerald-200"
            : status === "degraded"
            ? "bg-white border-amber-200"
            : "bg-white border-rose-200"
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="relative flex items-center justify-center">
              <span
                className={`w-4 h-4 rounded-full ${
                  status === "healthy"
                    ? "bg-emerald-500 shadow-[0_0_12px_#10b981]"
                    : status === "degraded"
                    ? "bg-amber-500 shadow-[0_0_12px_#f59e0b]"
                    : "bg-rose-500 shadow-[0_0_12px_#ef4444]"
                }`}
              />
              <span
                className={`absolute w-7 h-7 rounded-full animate-ping opacity-75 ${
                  status === "healthy"
                    ? "bg-emerald-400"
                    : status === "degraded"
                    ? "bg-amber-400"
                    : "bg-rose-400"
                }`}
              />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-black text-stone-900 uppercase tracking-tight">
                  System {status}
                </h2>
                {getStatusBadge(status)}
              </div>
              <p className="text-xs text-stone-500 mt-1">
                {status === "healthy"
                  ? "All mission-critical databases and microservices are operating optimally."
                  : status === "degraded"
                  ? "One or more non-critical components report degraded connectivity or offline status."
                  : "Primary backend database or server infrastructure is experiencing disruptions."}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 border-t md:border-t-0 md:border-l border-stone-100 pt-4 md:pt-0 md:pl-6">
            <div>
              <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Uptime</p>
              <p className="text-sm md:text-base font-black text-stone-800 mt-0.5">
                {system.uptime_human || "N/A"}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Memory</p>
              <p className="text-sm md:text-base font-black text-stone-800 mt-0.5">
                {system.memory_rss_mb ? `${system.memory_rss_mb} MB` : "N/A"}
              </p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Threads</p>
              <p className="text-sm md:text-base font-black text-stone-800 mt-0.5">
                {system.threads_count || "N/A"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Host System Specs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-white rounded-2xl border border-stone-200/80 shadow-sm">
          <div className="flex items-center gap-2 text-stone-400 text-xs mb-1">
            <Server size={14} />
            <span>Platform</span>
          </div>
          <p className="text-xs font-bold text-stone-800 truncate" title={system.platform}>
            {system.platform || "N/A"}
          </p>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-stone-200/80 shadow-sm">
          <div className="flex items-center gap-2 text-stone-400 text-xs mb-1">
            <Cpu size={14} />
            <span>Python Runtime</span>
          </div>
          <p className="text-xs font-bold text-stone-800">{system.python_version || "N/A"}</p>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-stone-200/80 shadow-sm">
          <div className="flex items-center gap-2 text-stone-400 text-xs mb-1">
            <Zap size={14} />
            <span>Process ID (PID)</span>
          </div>
          <p className="text-xs font-bold text-stone-800">{system.pid || "N/A"}</p>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-stone-200/80 shadow-sm">
          <div className="flex items-center gap-2 text-stone-400 text-xs mb-1">
            <Clock size={14} />
            <span>Started At</span>
          </div>
          <p className="text-xs font-bold text-stone-800 truncate">
            {system.started_at ? system.started_at.slice(0, 19).replace("T", " ") : "N/A"} UTC
          </p>
        </div>
      </div>

      {/* Subsystem Diagnostics Grid */}
      <div className="mb-4 flex items-center gap-2">
        <Layers size={18} className="text-stone-700" />
        <h3 className="text-base font-black text-stone-900">Subsystem &amp; Service Status</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {/* PostgreSQL */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database size={18} className="text-indigo-600" />
                <span className="font-bold text-sm text-stone-900">PostgreSQL</span>
              </div>
              {getStatusBadge(services.postgresql?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              {services.postgresql?.message || services.postgresql?.error || "Checking..."}
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Query Latency</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.postgresql?.latency_ms ?? 0} ms
            </span>
          </div>
        </div>

        {/* Redis */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap size={18} className="text-red-500" />
                <span className="font-bold text-sm text-stone-900">Redis Cache</span>
              </div>
              {getStatusBadge(services.redis?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              {services.redis?.message || services.redis?.error || "Checking..."}
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Ping Latency</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.redis?.latency_ms ?? 0} ms
            </span>
          </div>
        </div>

        {/* MongoDB */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database size={18} className="text-emerald-600" />
                <span className="font-bold text-sm text-stone-900">MongoDB NoSQL</span>
              </div>
              {getStatusBadge(services.mongodb?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              {services.mongodb?.message || services.mongodb?.error || "Checking..."}
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Admin Ping</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.mongodb?.latency_ms ?? 0} ms
            </span>
          </div>
        </div>

        {/* RabbitMQ */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity size={18} className="text-amber-500" />
                <span className="font-bold text-sm text-stone-900">RabbitMQ Broker</span>
              </div>
              {getStatusBadge(services.rabbitmq?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              {services.rabbitmq?.message || services.rabbitmq?.error || "Checking..."}
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Broker Latency</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.rabbitmq?.latency_ms ?? 0} ms
            </span>
          </div>
        </div>

        {/* User Agent */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Cpu size={18} className="text-blue-500" />
                <span className="font-bold text-sm text-stone-900">User Agent Graph</span>
              </div>
              {getStatusBadge(services.agents?.user_agent?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              Autonomous customer agent state machine, tool calls &amp; negotiations.
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Graph State</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.agents?.user_agent?.status || "Active"}
            </span>
          </div>
        </div>

        {/* Merchant Agent */}
        <div className="p-5 bg-white rounded-2xl border border-stone-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Cpu size={18} className="text-purple-500" />
                <span className="font-bold text-sm text-stone-900">Merchant Agent</span>
              </div>
              {getStatusBadge(services.agents?.merchant_agent?.status)}
            </div>
            <p className="text-xs text-stone-600 mb-4 min-h-[32px]">
              Store manager assistant for real-time inventory, pricing &amp; analytics.
            </p>
          </div>
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">
            <span>Graph State</span>
            <span className="font-mono font-bold text-stone-700 bg-stone-100 px-2 py-0.5 rounded">
              {services.agents?.merchant_agent?.status || "Active"}
            </span>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-center text-xs text-stone-400 pt-4 border-t border-stone-200">
        Dukaan Server Monitoring &bull; Last checked:{" "}
        {lastRefreshed ? lastRefreshed.toLocaleTimeString() : "Pending"}
      </div>
    </div>
  );
}

export default HealthPage;
