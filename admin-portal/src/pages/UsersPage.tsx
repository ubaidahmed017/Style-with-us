import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface UserResponse {
  user_id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
  is_blocked: boolean;
  blocked_until: string | null;
  block_reason: string | null;
}

const roleBadge = (role: string): string => {
  const m: Record<string, string> = {
    admin: 'bg-red-500/15 text-red-300 border border-red-500/30',
    brand: 'bg-fuchsia-500/15 text-fuchsia-300 border border-fuchsia-500/30',
    shopper: 'bg-brand-500/15 text-brand-300 border border-brand-500/30',
  };
  return m[role] ?? 'bg-white/10 text-gray-300';
};

export const UsersPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const qc = useQueryClient();
  const pageSize = 15;

  const { data: users, isLoading, error } = useQuery<UserResponse[]>({
    queryKey: ['users', page, roleFilter],
    queryFn: async () => {
      const rq = roleFilter ? `&role=${roleFilter}` : '';
      return (await api.get(`/admin/users?page=${page}&page_size=${pageSize}${rq}`)).data;
    },
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['users'] });
  const roleMut = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) => api.patch(`/admin/users/${id}?new_role=${role}`),
    onSuccess: invalidate, onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });
  const blockMut = useMutation({
    mutationFn: ({ id, days }: { id: string; days: number }) => {
      const reason = window.prompt('Reason (optional):') || undefined;
      return api.post(`/admin/users/${id}/block`, { duration_days: days, reason });
    },
    onSuccess: invalidate, onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });
  const unblockMut = useMutation({
    mutationFn: (id: string) => api.post(`/admin/users/${id}/unblock`),
    onSuccess: invalidate,
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/users/${id}`),
    onSuccess: invalidate, onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });

  const fmt = (d: string) => new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

  if (isLoading) {
    return <div className="flex justify-center items-center h-96"><div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  }
  if (error) return <div className="card p-6 border-red-500/40 text-red-300">Failed to load users.</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <p className="text-gray-400 text-sm">Manage roles and moderate accounts.</p>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Role</label>
          <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
            className="bg-ink-600 border border-white/10 rounded-lg text-white text-sm px-3 py-1.5 outline-none focus:ring-2 focus:ring-brand-500/40">
            <option value="">All Roles</option>
            <option value="shopper">Shopper</option>
            <option value="brand">Brand</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/5">
              <tr>
                {['Name', 'Email', 'Role', 'Status', 'Moderation'].map((h) => (
                  <th key={h} className="px-6 py-3.5 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {users && users.length > 0 ? users.map((u) => (
                <tr key={u.user_id} className="hover:bg-white/5 transition">
                  <td className="px-6 py-4 text-sm font-medium">{u.name}<div className="text-xs text-gray-500">{fmt(u.created_at)}</div></td>
                  <td className="px-6 py-4 text-sm text-gray-300">{u.email}</td>
                  <td className="px-6 py-4">
                    <select value={u.role} disabled={u.role === 'admin'}
                      onChange={(e) => { if (window.confirm(`Change role to ${e.target.value}?`)) roleMut.mutate({ id: u.user_id, role: e.target.value }); }}
                      className={`badge uppercase bg-transparent outline-none ${roleBadge(u.role)}`}>
                      <option value="shopper">shopper</option>
                      <option value="brand">brand</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="px-6 py-4">
                    {u.is_blocked
                      ? <span className="badge bg-red-500/15 text-red-300 border border-red-500/30" title={u.block_reason || ''}>
                          Blocked{u.blocked_until && u.blocked_until !== 'indefinite' ? ` · ${fmt(u.blocked_until)}` : u.blocked_until === 'indefinite' ? ' · indefinite' : ''}
                        </span>
                      : <span className="badge bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">Active</span>}
                  </td>
                  <td className="px-6 py-4">
                    {u.role === 'admin' ? (
                      <span className="text-xs text-gray-500">—</span>
                    ) : (
                      <div className="flex items-center gap-2">
                        {u.is_blocked ? (
                          <button onClick={() => unblockMut.mutate(u.user_id)} className="btn-ghost px-2.5 py-1 text-xs">Unblock</button>
                        ) : (
                          <select defaultValue="" onChange={(e) => { if (e.target.value) blockMut.mutate({ id: u.user_id, days: Number(e.target.value) }); e.currentTarget.value=''; }}
                            className="bg-ink-600 border border-white/10 rounded-lg text-white text-xs px-2 py-1 outline-none">
                            <option value="">Block…</option>
                            <option value="3">3 days</option>
                            <option value="7">7 days</option>
                            <option value="30">1 month</option>
                            <option value="0">Indefinite</option>
                          </select>
                        )}
                        <button onClick={() => { if (window.confirm(`Delete ${u.name}? This cannot be undone.`)) deleteMut.mutate(u.user_id); }}
                          className="px-2.5 py-1 text-xs rounded-lg border border-red-500/30 text-red-300 hover:bg-red-500/10">Delete</button>
                      </div>
                    )}
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 flex items-center justify-between border-t border-white/10">
          <button onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1} className="btn-ghost">Previous</button>
          <span className="text-gray-400 text-sm">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={!users || users.length < pageSize} className="btn-ghost">Next</button>
        </div>
      </div>
    </div>
  );
};
