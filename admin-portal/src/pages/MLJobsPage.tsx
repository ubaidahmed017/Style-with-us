import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api';

interface MLJob {
  job_id: string;
  user_id: string;
  job_type: string;
  status: string;
  created_at: string;
  input_image_url?: string;
  result_url?: string;
  error_message?: string;
}
interface MLJobStats { queued: number; processing: number; completed: number; failed: number; }

const statusBadge = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed': return 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30';
    case 'processing': return 'bg-brand-500/15 text-brand-300 border border-brand-500/30 animate-pulse';
    case 'queued':
    case 'uploaded': return 'bg-amber-500/15 text-amber-300 border border-amber-500/30';
    case 'failed': return 'bg-red-500/15 text-red-300 border border-red-500/30';
    default: return 'bg-white/10 text-gray-300';
  }
};

export const MLJobsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10000);
  const pageSize = 10;

  const { data: mlStats } = useQuery<MLJobStats>({
    queryKey: ['mlJobStatsPage'],
    queryFn: async () => (await api.get('/admin/analytics/ml-jobs')).data,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const { data: jobs, isLoading: jobsLoading, error, refetch } = useQuery<MLJob[]>({
    queryKey: ['mlJobsList', page, statusFilter],
    queryFn: async () => {
      const statusQuery = statusFilter ? `&status=${statusFilter}` : '';
      return (await api.get(`/admin/ml-jobs?page=${page}&page_size=${pageSize}${statusQuery}`)).data;
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const formatDate = (d: string) =>
    new Date(d).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

  const stats: [string, number, string][] = [
    ['Queued', mlStats?.queued ?? 0, 'text-amber-300'],
    ['Processing', mlStats?.processing ?? 0, 'text-brand-300'],
    ['Completed', mlStats?.completed ?? 0, 'text-emerald-300'],
    ['Failed', mlStats?.failed ?? 0, 'text-red-300'],
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <p className="text-gray-400 text-sm">Body-analysis and try-on job records.</p>
        <div className="flex flex-wrap items-center gap-3 card px-3 py-2">
          <span className="text-xs text-gray-400">Auto refresh</span>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`relative inline-flex h-5 w-10 rounded-full transition ${autoRefresh ? 'bg-brand-500' : 'bg-white/15'}`}
          >
            <span className={`inline-block h-4 w-4 mt-0.5 rounded-full bg-white transition ${autoRefresh ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </button>
          <select
            value={refreshInterval} onChange={(e) => setRefreshInterval(Number(e.target.value))}
            disabled={!autoRefresh}
            className="bg-ink-600 border border-white/10 rounded-lg text-white text-xs py-1 px-1.5 outline-none disabled:opacity-50"
          >
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
          </select>
          <button onClick={() => refetch()} className="btn-ghost px-2.5 py-1 text-xs">↻ Refresh</button>
        </div>
      </div>

      {/* Queue stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(([label, value, color]) => (
          <div key={label} className="card p-4 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</span>
            <span className={`text-2xl font-extrabold ${color}`}>{value}</span>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="status-filter" className="text-sm text-gray-400">Status</label>
        <select
          id="status-filter" value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="bg-ink-600 border border-white/10 rounded-lg text-white text-sm px-3 py-1.5 outline-none focus:ring-2 focus:ring-brand-500/40"
        >
          <option value="">All Statuses</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/5">
              <tr>
                {['Job ID', 'Type', 'Status', 'Submitted', 'Input', 'Result / Error'].map((h) => (
                  <th key={h} className="px-6 py-3.5 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {jobsLoading && !jobs ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                  <div className="flex justify-center items-center gap-2">
                    <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                    Loading…
                  </div>
                </td></tr>
              ) : error ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-red-300">Failed to fetch jobs. Is the backend running?</td></tr>
              ) : jobs && jobs.length > 0 ? jobs.map((job) => (
                <tr key={job.job_id} className="hover:bg-white/5 transition">
                  <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-400">{job.job_id.slice(0, 8)}…</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold capitalize">{job.job_type.replace('_', ' ')}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge uppercase ${statusBadge(job.status)}`}>{job.status}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-400">{formatDate(job.created_at)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {job.input_image_url
                      ? <a href={job.input_image_url} target="_blank" rel="noreferrer" className="text-brand-300 hover:text-brand-100 underline text-xs">View</a>
                      : <span className="text-gray-500 text-xs">N/A</span>}
                  </td>
                  <td className="px-6 py-4 text-sm max-w-xs truncate">
                    {job.status === 'completed' && job.result_url
                      ? <a href={job.result_url} target="_blank" rel="noreferrer" className="text-emerald-300 hover:text-emerald-100 underline text-xs">Output</a>
                      : job.status === 'failed' && job.error_message
                        ? <span className="text-red-300 text-xs" title={job.error_message}>{job.error_message}</span>
                        : <span className="text-gray-500 text-xs">—</span>}
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-500 text-sm">No jobs found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 flex items-center justify-between border-t border-white/10">
          <button onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1} className="btn-ghost">Previous</button>
          <span className="text-gray-400 text-sm">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={!jobs || jobs.length < pageSize} className="btn-ghost">Next</button>
        </div>
      </div>
    </div>
  );
};
