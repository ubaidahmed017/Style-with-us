import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface Overview {
  commission_percent: number;
  total_gross_sales: number;
  total_commission: number;
  total_brand_net: number;
  total_paid_out: number;
  total_owed_to_brands: number;
  subscription_active_count: number;
  subscription_revenue: number;
  total_platform_revenue: number;
}
interface Earning {
  brand_id: string;
  company_name: string;
  status: string;
  gross_sales: number;
  commission_percent: number;
  commission_amount: number;
  net_earning: number;
  paid: number;
  remaining: number;
}

const money = (n: number) => `$${(n ?? 0).toFixed(2)}`;

const Stat: React.FC<{ label: string; value: string; tint?: string }> = ({ label, value, tint }) => (
  <div className="card p-5">
    <div className="text-xs font-semibold uppercase tracking-wider text-gray-400">{label}</div>
    <div className={`text-2xl font-extrabold mt-2 ${tint ?? ''}`}>{value}</div>
  </div>
);

export const FinancePage: React.FC = () => {
  const qc = useQueryClient();
  const { data: overview } = useQuery<Overview>({
    queryKey: ['finance'], queryFn: async () => (await api.get('/admin/finance')).data, refetchInterval: 30000,
  });
  const { data: earnings } = useQuery<Earning[]>({
    queryKey: ['earnings'], queryFn: async () => (await api.get('/admin/earnings')).data, refetchInterval: 30000,
  });

  const [pct, setPct] = useState<string>('');
  useEffect(() => { if (overview && pct === '') setPct(String(overview.commission_percent)); }, [overview]); // eslint-disable-line

  const saveCommission = useMutation({
    mutationFn: () => api.patch('/admin/settings', { commission_percent: Number(pct) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['finance'] }); qc.invalidateQueries({ queryKey: ['earnings'] }); },
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });
  const payout = useMutation({
    mutationFn: ({ id, amount }: { id: string; amount: number }) => api.post(`/admin/brands/${id}/payouts`, { amount }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['earnings'] }); qc.invalidateQueries({ queryKey: ['finance'] }); },
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });

  const recordPayout = (e: Earning) => {
    const raw = window.prompt(`Record payout to ${e.company_name}. Amount owed: ${money(e.remaining)}`, String(e.remaining > 0 ? e.remaining : ''));
    if (!raw) return;
    const amount = Number(raw);
    if (!(amount > 0)) return alert('Enter a positive amount.');
    payout.mutate({ id: e.brand_id, amount });
  };

  return (
    <div className="space-y-8">
      {/* Overview */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <Stat label="Platform revenue" value={money(overview?.total_platform_revenue ?? 0)} tint="text-emerald-300" />
        <Stat label="Commission earned" value={money(overview?.total_commission ?? 0)} tint="text-brand-300" />
        <Stat label="Subscription revenue" value={money(overview?.subscription_revenue ?? 0)} tint="text-fuchsia-300" />
        <Stat label="Gross sales (GMV)" value={money(overview?.total_gross_sales ?? 0)} />
        <Stat label="Owed to brands" value={money(overview?.total_owed_to_brands ?? 0)} tint="text-amber-300" />
        <Stat label="Paid out" value={money(overview?.total_paid_out ?? 0)} />
        <Stat label="Active subscribers" value={String(overview?.subscription_active_count ?? 0)} />
      </div>

      {/* Commission control */}
      <div className="card p-6">
        <h2 className="text-lg font-bold mb-1">Commission rate</h2>
        <p className="text-sm text-gray-400 mb-4">Applied to every brand's sales. Updates all earnings immediately.</p>
        <div className="flex items-center gap-3 max-w-xs">
          <div className="relative flex-1">
            <input type="number" min={0} max={100} step="0.5" value={pct} onChange={(e) => setPct(e.target.value)}
              className="bg-ink-600 border border-white/10 rounded-xl text-white px-3 py-2.5 w-full outline-none focus:ring-2 focus:ring-brand-500/40" />
            <span className="absolute right-3 top-2.5 text-gray-400">%</span>
          </div>
          <button onClick={() => saveCommission.mutate()} className="btn-primary">Save</button>
        </div>
      </div>

      {/* Per-brand earnings */}
      <div className="card overflow-hidden">
        <div className="px-6 pt-5 pb-3"><h2 className="text-lg font-bold">Brand earnings</h2></div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/5">
              <tr>
                {['Brand', 'Gross', 'Commission', 'Net', 'Paid', 'Remaining', ''].map((h) => (
                  <th key={h} className="px-6 py-3.5 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {earnings && earnings.length > 0 ? earnings.map((e) => (
                <tr key={e.brand_id} className="hover:bg-white/5 transition">
                  <td className="px-6 py-4 text-sm font-semibold">{e.company_name}</td>
                  <td className="px-6 py-4 text-sm">{money(e.gross_sales)}</td>
                  <td className="px-6 py-4 text-sm text-brand-300">{money(e.commission_amount)} <span className="text-gray-500">({e.commission_percent}%)</span></td>
                  <td className="px-6 py-4 text-sm">{money(e.net_earning)}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{money(e.paid)}</td>
                  <td className="px-6 py-4 text-sm font-bold text-amber-300">{money(e.remaining)}</td>
                  <td className="px-6 py-4">
                    <button onClick={() => recordPayout(e)} disabled={e.remaining <= 0} className="btn-ghost px-3 py-1.5 text-xs disabled:opacity-40">
                      {e.remaining <= 0 ? 'Paid' : 'Record payout'}
                    </button>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-500 text-sm">No brand earnings yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
