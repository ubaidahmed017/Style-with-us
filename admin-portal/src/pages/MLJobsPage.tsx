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

interface MLJobStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
}

export const MLJobsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10000); // 10s
  const pageSize = 10;

  // Fetch ML Job queue stats
  const { data: mlStats } = useQuery<MLJobStats>({
    queryKey: ['mlJobStatsPage'],
    queryFn: async () => {
      const res = await api.get('/admin/analytics/ml-jobs');
      return res.data;
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  // Fetch ML Jobs paginated list
  const { data: jobs, isLoading: jobsLoading, error, refetch } = useQuery<MLJob[]>({
    queryKey: ['mlJobsList', page, statusFilter],
    queryFn: async () => {
      const statusQuery = statusFilter ? `&status=${statusFilter}` : '';
      const res = await api.get(`/admin/ml-jobs?page=${page}&page_size=${pageSize}${statusQuery}`);
      return res.data;
    },
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-500/20 text-green-400 border border-green-500/30';
      case 'processing':
        return 'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse';
      case 'queued':
      case 'uploaded':
        return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
      case 'failed':
        return 'bg-red-500/20 text-red-400 border border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border border-gray-500/30';
    }
  };

  const stats = [
    { label: 'Queued', value: mlStats?.queued ?? 0, bg: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' },
    { label: 'Processing', value: mlStats?.processing ?? 0, bg: 'bg-blue-500/10 text-blue-500 border-blue-500/20' },
    { label: 'Completed', value: mlStats?.completed ?? 0, bg: 'bg-green-500/10 text-green-500 border-green-500/20' },
    { label: 'Failed', value: mlStats?.failed ?? 0, bg: 'bg-red-500/10 text-red-500 border-red-500/20' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">ML Job Queue Monitor</h1>
          <p className="text-gray-400 text-sm mt-1">Real-time status of body shape analysis and virtual try-on tasks</p>
        </div>

        {/* Real-time controls */}
        <div className="flex flex-wrap items-center gap-3 bg-gray-800 p-2 rounded-lg border border-gray-700/50">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400 font-medium">Auto Refresh:</span>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`relative inline-flex h-5 w-10 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                autoRefresh ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  autoRefresh ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          <div className="h-4 w-px bg-gray-750"></div>

          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            disabled={!autoRefresh}
            className="bg-gray-700 border border-gray-600 rounded text-white text-xs py-1 px-1.5 focus:outline-none disabled:opacity-50"
          >
            <option value={5000}>Every 5s</option>
            <option value={10000}>Every 10s</option>
            <option value={30000}>Every 30s</option>
          </select>

          <button
            onClick={() => refetch()}
            className="px-2 py-1 bg-gray-750 hover:bg-gray-700 border border-gray-650 rounded text-xs font-semibold text-gray-200 transition"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Queue Status Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <div key={i} className={`bg-gray-800 p-4 rounded-lg border border-gray-700/30 flex justify-between items-center shadow-md`}>
            <span className="text-gray-400 text-sm font-semibold uppercase">{stat.label}</span>
            <span className={`px-2.5 py-1 rounded text-lg font-bold ${stat.bg}`}>{stat.value}</span>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <label htmlFor="status-filter" className="text-sm font-semibold text-gray-300">
            Filter by Status:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700/50">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-750">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Job ID</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Job Type</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Submitted At</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Input Image</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Result / Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 bg-gray-800">
              {jobsLoading && !jobs ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                    <div className="flex justify-center items-center">
                      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
                      Loading jobs list...
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-red-400">
                    Failed to fetch jobs list. Make sure the backend server is running.
                  </td>
                </tr>
              ) : jobs && jobs.length > 0 ? (
                jobs.map((job) => (
                  <tr key={job.job_id} className="hover:bg-gray-750/30">
                    <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-400">{job.job_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-white capitalize">
                      {job.job_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${getStatusBadgeClass(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-400">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {job.input_image_url ? (
                        <a
                          href={job.input_image_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-400 hover:text-blue-300 font-medium underline text-xs"
                        >
                          View Image
                        </a>
                      ) : (
                        <span className="text-gray-500 text-xs">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm max-w-xs truncate">
                      {job.status === 'completed' && job.result_url ? (
                        <a
                          href={job.result_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-green-400 hover:text-green-300 font-medium underline text-xs"
                        >
                          View Output
                        </a>
                      ) : job.status === 'failed' && job.error_message ? (
                        <span className="text-red-400 text-xs font-medium" title={job.error_message}>
                          {job.error_message}
                        </span>
                      ) : (
                        <span className="text-gray-500 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500 text-sm">
                    No jobs found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="bg-gray-750 px-6 py-4 flex items-center justify-between border-t border-gray-700">
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <span className="text-gray-400 text-sm">Page {page}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!jobs || jobs.length < pageSize}
            className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
