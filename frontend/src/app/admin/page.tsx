"use client";

import { useQuery } from "@tanstack/react-query";
import { getAnalytics, getActivityLogs } from "@/lib/admin";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function formatTimeAgo(dateString: string) {
  const diff = Date.now() - new Date(dateString).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function AdminDashboardPage() {
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["admin", "analytics"],
    queryFn: getAnalytics,
    refetchInterval: 30000,
  });

  const { data: activityLogs, isLoading: activityLoading } = useQuery({
    queryKey: ["admin", "activity"],
    queryFn: getActivityLogs,
    refetchInterval: 15000,
  });

  const handleExportCSV = () => {
    if (!analytics) return;
    const csvRows = [
      ["Metric", "Value"],
      ["Total Users", analytics.kpis.total_users],
      ["Active Users", analytics.kpis.active_users],
      ["Total Predictions", analytics.kpis.total_predictions],
      ["Predictions Today", analytics.kpis.predictions_today],
      ["Success Rate (%)", analytics.kpis.success_rate_percent],
    ];
    
    const csvContent = csvRows.map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "analytics_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (analyticsLoading || activityLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">System Overview</h1>
          <p className="text-zinc-400 mt-1">Real-time platform metrics and health status.</p>
        </div>
        <button
          onClick={handleExportCSV}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-2 px-4 rounded-xl transition-colors border border-zinc-700 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
          Export CSV
        </button>
      </header>

      {/* KPIs Grid */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Total Users" value={analytics.kpis.total_users} />
          <StatCard title="Active Users" value={analytics.kpis.active_users} highlight />
          <StatCard title="Total Predictions" value={analytics.kpis.total_predictions} />
          <StatCard title="Success Rate" value={`${analytics.kpis.success_rate_percent.toFixed(1)}%`} />
        </div>
      )}

      {/* Charts Row */}
      {analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-zinc-100 mb-4">Most Searched Brands</h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.kpis.most_searched_brands}>
                  <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip cursor={{fill: '#27272a'}} contentStyle={{backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5', borderRadius: '8px'}} />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-zinc-100 mb-4">City-wise Breakdowns</h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.kpis.city_breakdowns}>
                  <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip cursor={{fill: '#27272a'}} contentStyle={{backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5', borderRadius: '8px'}} />
                  <Bar dataKey="count" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Feed */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold text-zinc-100">Live Activity Feed</h2>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl">
            {activityLogs && activityLogs.length > 0 ? (
              <ul className="divide-y divide-zinc-800/50 max-h-[500px] overflow-y-auto custom-scrollbar">
                {activityLogs.map((log) => (
                  <li key={log.id} className="p-4 hover:bg-zinc-800/20 transition-colors">
                    <div className="flex items-start gap-4">
                      <div className="w-2 h-2 mt-2 rounded-full bg-indigo-500 flex-shrink-0"></div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-zinc-200 uppercase tracking-wider text-xs mb-1 text-indigo-400">
                          {log.action.replace(/_/g, " ")}
                        </p>
                        <p className="text-sm text-zinc-400 truncate">
                          {log.entity_type} {log.entity_id ? `(${log.entity_id})` : ""}
                        </p>
                      </div>
                      <time className="text-xs text-zinc-500 whitespace-nowrap">
                        {formatTimeAgo(log.created_at)}
                      </time>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-8 text-center text-zinc-500">No recent activity.</div>
            )}
          </div>
        </div>

        {/* Health Status */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-zinc-100">System Health</h2>
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl space-y-6">
            <HealthItem 
              label="API Status" 
              status={analytics?.health.api_status} 
              isGood={analytics?.health.api_status === "operational"} 
            />
            <HealthItem 
              label="API Latency" 
              status={`${analytics?.health.api_latency_ms || 0} ms`} 
              isGood={(analytics?.health.api_latency_ms || 0) < 500} 
            />
            <HealthItem 
              label="Database" 
              status={analytics?.health.db_status} 
              isGood={analytics?.health.db_status === "operational"} 
            />
            <HealthItem 
              label="Cloudinary Storage" 
              status={analytics?.health.cloudinary_status} 
              isGood={analytics?.health.cloudinary_status === "operational"} 
            />
            <HealthItem 
              label="Active ML Model" 
              status={analytics?.health.active_model_version || "None"} 
              isGood={!!analytics?.health.active_model_version} 
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, highlight = false }: { title: string; value: string | number; highlight?: boolean }) {
  return (
    <div className={`p-6 rounded-2xl border backdrop-blur-xl ${highlight ? 'bg-indigo-500/10 border-indigo-500/20 shadow-[0_0_30px_rgba(99,102,241,0.1)]' : 'bg-zinc-900/50 border-zinc-800/50'}`}>
      <p className="text-sm font-medium text-zinc-400 mb-2">{title}</p>
      <p className={`text-3xl font-bold tracking-tight ${highlight ? 'text-indigo-400' : 'text-zinc-100'}`}>
        {value}
      </p>
    </div>
  );
}

function HealthItem({ label, status, isGood }: { label: string; status?: string; isGood: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-zinc-400 text-sm">{label}</span>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isGood ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
        <span className={`text-sm font-medium ${isGood ? 'text-emerald-400' : 'text-red-400'}`}>
          {status || "Unknown"}
        </span>
      </div>
    </div>
  );
}
