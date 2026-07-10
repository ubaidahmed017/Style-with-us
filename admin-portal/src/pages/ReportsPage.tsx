import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface Report {
  report_id: string;
  reporter_role: string;
  reporter_name: string | null;
  reporter_email: string | null;
  target_type: string;
  target_id: string | null;
  subject: string;
  message: string;
  status: string;
  admin_note: string | null;
  created_at: string;
}

const statusBadge = (s: string): string => {
  const m: Record<string, string> = {
    open: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
    resolved: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    dismissed: 'bg-white/10 text-gray-400 border border-white/10',
  };
  return m[s] ?? 'bg-white/10 text-gray-300';
};

export const ReportsPage: React.FC = () => {
  const [status, setStatus] = useState('');
  const qc = useQueryClient();

  const { data: reports, isLoading, error } = useQuery<Report[]>({
    queryKey: ['reports', status],
    queryFn: async () => (await api.get(`/admin/reports${status ? `?status_filter=${status}` : ''}`)).data,
  });

  const update = useMutation({
    mutationFn: ({ id, status, note }: { id: string; status: string; note?: string }) =>
      api.patch(`/admin/reports/${id}`, { status, admin_note: note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports'] }),
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });

  const act = (id: string, status: string) => {
    const note = window.prompt('Admin note (optional):') || undefined;
    update.mutate({ id, status, note });
  };

  if (isLoading) return <div className="flex justify-center items-center h-96"><div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (error) return <div className="card p-6 border-red-500/40 text-red-300">Failed to load reports.</div>;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-400">Status</label>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="bg-ink-600 border border-white/10 rounded-lg text-white text-sm px-3 py-1.5 outline-none focus:ring-2 focus:ring-brand-500/40">
          <option value="">All</option>
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {reports && reports.length > 0 ? reports.map((r) => (
        <div key={r.report_id} className="card p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold">{r.subject}</span>
                <span className={`badge uppercase ${statusBadge(r.status)}`}>{r.status}</span>
                <span className="badge bg-white/5 text-gray-400 border border-white/10">{r.target_type}</span>
              </div>
              <p className="text-sm text-gray-300 mt-2">{r.message}</p>
              <p className="text-xs text-gray-500 mt-2">
                by {r.reporter_name || 'user'} ({r.reporter_role}) · {r.reporter_email} · {new Date(r.created_at).toLocaleString()}
              </p>
              {r.admin_note && <p className="text-xs text-brand-300 mt-1">Note: {r.admin_note}</p>}
            </div>
            {r.status === 'open' && (
              <div className="flex flex-col gap-2 shrink-0">
                <button onClick={() => act(r.report_id, 'resolved')} className="btn-primary px-3 py-1.5 text-xs">Resolve</button>
                <button onClick={() => act(r.report_id, 'dismissed')} className="btn-ghost px-3 py-1.5 text-xs">Dismiss</button>
              </div>
            )}
          </div>
        </div>
      )) : (
        <div className="card p-12 text-center text-gray-500 text-sm">No reports.</div>
      )}
    </div>
  );
};
