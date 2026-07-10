import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface BrandInfo {
  brand_id: string;
  user_id: string;
  company_name: string;
  logo_url: string | null;
  status: string;
  rejection_reason: string | null;
  product_count: number;
}

const statusBadge = (s: string) => {
  const map: Record<string, string> = {
    approved: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    pending: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
    rejected: 'bg-red-500/15 text-red-300 border border-red-500/30',
  };
  return map[s] ?? 'bg-white/10 text-gray-300';
};

export const BrandsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const pageSize = 15;
  const qc = useQueryClient();

  const { data: brands, isLoading, error } = useQuery<BrandInfo[]>({
    queryKey: ['brands', page],
    queryFn: async () => (await api.get(`/admin/brands?page=${page}&page_size=${pageSize}`)).data,
  });

  const approve = useMutation({
    mutationFn: (id: string) => api.post(`/admin/brands/${id}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['brands'] }),
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed to approve'),
  });
  const reject = useMutation({
    mutationFn: (id: string) => {
      const reason = window.prompt('Reason for rejection (optional):') || undefined;
      return api.post(`/admin/brands/${id}/reject`, { reason });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['brands'] }),
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed to reject'),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (error) return <div className="card p-6 border-red-500/40 text-red-300">Failed to load brands.</div>;

  return (
    <div className="space-y-6">
      <p className="text-gray-400 text-sm">Approve new brands and manage partners.</p>
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/5">
              <tr>
                {['Logo', 'Company', 'Status', 'Products', 'Actions'].map((h) => (
                  <th key={h} className="px-6 py-3.5 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {brands && brands.length > 0 ? brands.map((b) => (
                <tr key={b.brand_id} className="hover:bg-white/5 transition">
                  <td className="px-6 py-4">
                    {b.logo_url ? (
                      <img src={b.logo_url} alt="" className="w-10 h-10 object-contain rounded-lg bg-white/5 p-1 border border-white/10" />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-brand-gradient grid place-items-center font-bold">
                        {b.company_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold">
                    {b.company_name}
                    {b.rejection_reason && (
                      <div className="text-xs text-red-300/80 mt-0.5">Rejected: {b.rejection_reason}</div>
                    )}
                  </td>
                  <td className="px-6 py-4"><span className={`badge uppercase ${statusBadge(b.status)}`}>{b.status}</span></td>
                  <td className="px-6 py-4 text-sm">{b.product_count}</td>
                  <td className="px-6 py-4">
                    {b.status !== 'approved' && (
                      <button onClick={() => approve.mutate(b.brand_id)} className="btn-primary px-3 py-1.5 text-xs mr-2">Approve</button>
                    )}
                    {b.status !== 'rejected' && (
                      <button onClick={() => reject.mutate(b.brand_id)} className="btn-ghost px-3 py-1.5 text-xs">Reject</button>
                    )}
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">No brand partners yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 flex items-center justify-between border-t border-white/10">
          <button onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1} className="btn-ghost">Previous</button>
          <span className="text-gray-400 text-sm">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={!brands || brands.length < pageSize} className="btn-ghost">Next</button>
        </div>
      </div>
    </div>
  );
};
