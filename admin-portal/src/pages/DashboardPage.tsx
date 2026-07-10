import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  PieChart, Pie, Cell,
} from 'recharts';
import api from '../api';

interface OverviewData {
  total_users: number;
  total_brands: number;
  total_orders: number;
  total_revenue: number;
  active_ml_jobs: number;
}
interface MLJobStats { queued: number; processing: number; completed: number; failed: number; }
interface SalesDataPoint { date: string; revenue: number; }

const tooltipStyle = {
  backgroundColor: '#1a1a2e',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 12,
  color: '#fff',
};

const StatCard: React.FC<{ label: string; value: string | number; icon: React.ReactNode; tint: string }>
  = ({ label, value, icon, tint }) => (
  <div className="card p-5">
    <div className="flex items-center justify-between">
      <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</span>
      <div className={`w-9 h-9 rounded-xl grid place-items-center ${tint}`}>{icon}</div>
    </div>
    <div className="text-3xl font-extrabold mt-3">{value}</div>
  </div>
);

const dot = (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <circle cx="12" cy="12" r="8" />
  </svg>
);

export const DashboardPage: React.FC = () => {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery<OverviewData>({
    queryKey: ['analyticsOverview'],
    queryFn: async () => (await api.get('/admin/analytics/overview')).data,
    refetchInterval: 30000,
  });
  const { data: mlStats, isLoading: mlLoading } = useQuery<MLJobStats>({
    queryKey: ['mlJobStats'],
    queryFn: async () => (await api.get('/admin/analytics/ml-jobs')).data,
    refetchInterval: 30000,
  });
  const { data: salesData, isLoading: salesLoading } = useQuery<SalesDataPoint[]>({
    queryKey: ['salesOverTime'],
    queryFn: async () => (await api.get('/admin/analytics/sales-over-time?days=30')).data,
    refetchInterval: 30000,
  });

  if (overviewLoading || mlLoading || salesLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <span className="ml-3 text-gray-400">Loading dashboard…</span>
      </div>
    );
  }
  if (overviewError) {
    return (
      <div className="card p-6 border-red-500/40 text-red-300">
        Failed to load statistics. Make sure the backend is running and the database is reachable.
      </div>
    );
  }

  const stats = [
    { label: 'Total Users', value: overview?.total_users ?? 0, tint: 'bg-brand-500/20 text-brand-300' },
    { label: 'Brands', value: overview?.total_brands ?? 0, tint: 'bg-fuchsia-500/20 text-fuchsia-300' },
    { label: 'Orders', value: overview?.total_orders ?? 0, tint: 'bg-indigo-500/20 text-indigo-300' },
    { label: 'Revenue', value: `$${(overview?.total_revenue ?? 0).toFixed(2)}`, tint: 'bg-emerald-500/20 text-emerald-300' },
    { label: 'Active ML Jobs', value: overview?.active_ml_jobs ?? 0, tint: 'bg-amber-500/20 text-amber-300' },
  ];

  const pieData = mlStats ? [
    { name: 'Completed', value: mlStats.completed, color: '#2ECC71' },
    { name: 'Processing', value: mlStats.processing, color: '#6C63FF' },
    { name: 'Queued', value: mlStats.queued, color: '#F39C12' },
    { name: 'Failed', value: mlStats.failed, color: '#E74C3C' },
  ].filter((d) => d.value > 0) : [];

  return (
    <div className="space-y-8">
      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((s) => (
          <StatCard key={s.label} label={s.label} value={s.value} icon={dot} tint={s.tint} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales */}
        <div className="lg:col-span-2 card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">Sales · last 30 days</h2>
            <span className="badge bg-emerald-500/15 text-emerald-300">Revenue</span>
          </div>
          <div className="h-80">
            {salesData && salesData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={salesData}>
                  <defs>
                    <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6C63FF" stopOpacity={0.6} />
                      <stop offset="100%" stopColor="#6C63FF" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="revenue" name="Revenue ($)"
                    stroke="#6C63FF" strokeWidth={3} fill="url(#rev)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No sales data yet.
              </div>
            )}
          </div>
        </div>

        {/* ML queue */}
        <div className="card p-6">
          <h2 className="text-lg font-bold mb-4">ML queue</h2>
          <div className="h-56">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={58} outerRadius={80}
                    paddingAngle={4} dataKey="value">
                    {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No active jobs.
              </div>
            )}
          </div>
          <div className="mt-4 space-y-2">
            {[
              ['Completed', mlStats?.completed ?? 0, '#2ECC71'],
              ['Processing', mlStats?.processing ?? 0, '#6C63FF'],
              ['Queued', mlStats?.queued ?? 0, '#F39C12'],
              ['Failed', mlStats?.failed ?? 0, '#E74C3C'],
            ].map(([label, val, color]) => (
              <div key={label as string} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-gray-300">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: color as string }} />
                  {label}
                </span>
                <span className="font-semibold">{val as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
