import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import api from '../api';

interface OverviewData {
  total_users: number;
  total_brands: number;
  total_orders: number;
  total_revenue: number;
  active_ml_jobs: number;
}

interface MLJobStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
}

interface SalesDataPoint {
  date: string;
  revenue: number;
}

export const DashboardPage: React.FC = () => {
  // Fetch Analytics Overview
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery<OverviewData>({
    queryKey: ['analyticsOverview'],
    queryFn: async () => {
      const res = await api.get('/admin/analytics/overview');
      return res.data;
    },
    refetchInterval: 30000, // 30s auto-refresh
  });

  // Fetch ML Job queue stats
  const { data: mlStats, isLoading: mlLoading } = useQuery<MLJobStats>({
    queryKey: ['mlJobStats'],
    queryFn: async () => {
      const res = await api.get('/admin/analytics/ml-jobs');
      return res.data;
    },
    refetchInterval: 30000, // 30s auto-refresh
  });

  // Fetch Sales Over Time (last 30 days)
  const { data: salesData, isLoading: salesLoading } = useQuery<SalesDataPoint[]>({
    queryKey: ['salesOverTime'],
    queryFn: async () => {
      const res = await api.get('/admin/analytics/sales-over-time?days=30');
      return res.data;
    },
    refetchInterval: 30000, // 30s auto-refresh
  });

  if (overviewLoading || mlLoading || salesLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="ml-3 text-gray-400">Loading dashboard...</span>
      </div>
    );
  }

  if (overviewError) {
    return (
      <div className="p-6 bg-red-900/30 border border-red-500 text-red-200 rounded-md">
        Failed to load dashboard statistics. Make sure the backend server is running and database is accessible.
      </div>
    );
  }

  const statCards = [
    { label: 'Total Users', value: overview?.total_users ?? 0, icon: '👥', color: 'border-blue-500' },
    { label: 'Registered Brands', value: overview?.total_brands ?? 0, icon: '🏢', color: 'border-purple-500' },
    { label: 'Total Orders', value: overview?.total_orders ?? 0, icon: '🛍️', color: 'border-indigo-500' },
    { label: 'Total Revenue', value: `$${(overview?.total_revenue ?? 0).toFixed(2)}`, icon: '💵', color: 'border-green-500' },
    { label: 'Active ML Jobs', value: overview?.active_ml_jobs ?? 0, icon: '⚡', color: 'border-orange-500' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard Overview</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time platform metrics (refreshes every 30s)</p>
      </div>

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {statCards.map((card, index) => (
          <div
            key={index}
            className={`bg-gray-800 rounded-lg p-6 border-l-4 ${card.color} shadow-lg border border-gray-700/50`}
          >
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm font-semibold uppercase">{card.label}</span>
              <span className="text-2xl">{card.icon}</span>
            </div>
            <div className="text-2xl font-bold mt-2 text-white">{card.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sales Chart (2/3 width on wide screens) */}
        <div className="lg:col-span-2 bg-gray-800 p-6 rounded-lg border border-gray-700/50 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4">Sales Performance (Last 30 Days)</h2>
          <div className="h-80">
            {salesData && salesData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={salesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} tickLine={false} />
                  <YAxis stroke="#9CA3AF" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#FFF' }}
                    labelClassName="font-bold"
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Daily Sales ($)"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No sales data available.
              </div>
            )}
          </div>
        </div>

        {/* ML Job Queue Widget (1/3 width) */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700/50 shadow-lg">
          <h2 className="text-xl font-bold text-white mb-4">ML Worker Queue Status</h2>
          <div className="h-80">
            {mlStats && (mlStats.completed > 0 || mlStats.processing > 0 || mlStats.queued > 0 || mlStats.failed > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Completed', value: mlStats.completed, color: '#10B981' },
                      { name: 'Processing', value: mlStats.processing, color: '#3B82F6' },
                      { name: 'Queued', value: mlStats.queued, color: '#F59E0B' },
                      { name: 'Failed', value: mlStats.failed, color: '#EF4444' },
                    ].filter(item => item.value > 0)}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {[
                      { name: 'Completed', value: mlStats.completed, color: '#10B981' },
                      { name: 'Processing', value: mlStats.processing, color: '#3B82F6' },
                      { name: 'Queued', value: mlStats.queued, color: '#F59E0B' },
                      { name: 'Failed', value: mlStats.failed, color: '#EF4444' },
                    ].filter(item => item.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#FFF' }}
                    itemStyle={{ color: '#FFF' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No active ML Jobs.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
