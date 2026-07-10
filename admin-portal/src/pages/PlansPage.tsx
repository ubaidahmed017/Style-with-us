import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface Plan {
  plan_id: string;
  name: string;
  price: number;
  interval: string;
  features: string | null;
  is_active: boolean;
}

export const PlansPage: React.FC = () => {
  const qc = useQueryClient();
  const { data: plans, isLoading, error } = useQuery<Plan[]>({
    queryKey: ['plans'], queryFn: async () => (await api.get('/admin/subscription-plans')).data,
  });

  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [interval, setInterval] = useState('month');
  const [features, setFeatures] = useState('');

  const invalidate = () => qc.invalidateQueries({ queryKey: ['plans'] });
  const create = useMutation({
    mutationFn: () => api.post('/admin/subscription-plans', {
      name, price: Number(price), interval, features: features || null, is_active: true,
    }),
    onSuccess: () => { invalidate(); setName(''); setPrice(''); setFeatures(''); },
    onError: (e: any) => alert(e.response?.data?.detail || 'Failed'),
  });
  const toggle = useMutation({
    mutationFn: (p: Plan) => api.patch(`/admin/subscription-plans/${p.plan_id}`, { is_active: !p.is_active }),
    onSuccess: invalidate,
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/subscription-plans/${id}`),
    onSuccess: invalidate,
  });

  if (isLoading) return <div className="flex justify-center items-center h-96"><div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (error) return <div className="card p-6 border-red-500/40 text-red-300">Failed to load plans.</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Create */}
      <div className="card p-6 lg:col-span-1 h-fit">
        <h2 className="text-lg font-bold mb-4">New plan</h2>
        <div className="space-y-3">
          <input className="field" placeholder="Name (e.g. Premium)" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="flex gap-2">
            <input className="field" type="number" min={0} step="0.01" placeholder="Price" value={price} onChange={(e) => setPrice(e.target.value)} />
            <select className="field" value={interval} onChange={(e) => setInterval(e.target.value)}>
              <option value="month">/ month</option>
              <option value="year">/ year</option>
            </select>
          </div>
          <textarea className="field" rows={4} placeholder="Features (one per line)" value={features} onChange={(e) => setFeatures(e.target.value)} />
          <button onClick={() => name && price && create.mutate()} className="btn-primary w-full">Create plan</button>
        </div>
      </div>

      {/* List */}
      <div className="lg:col-span-2 space-y-4">
        {plans && plans.length > 0 ? plans.map((p) => (
          <div key={p.plan_id} className={`card p-5 ${!p.is_active ? 'opacity-60' : ''}`}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg">{p.name}</span>
                  {!p.is_active && <span className="badge bg-white/10 text-gray-400">inactive</span>}
                </div>
                <div className="text-brand-300 font-semibold mt-0.5">${p.price.toFixed(2)}<span className="text-gray-500"> / {p.interval}</span></div>
                {p.features && (
                  <ul className="mt-3 space-y-1">
                    {p.features.split('\n').filter(Boolean).map((f, i) => (
                      <li key={i} className="text-sm text-gray-300 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-400" />{f}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                <button onClick={() => toggle.mutate(p)} className="btn-ghost px-3 py-1.5 text-xs">
                  {p.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button onClick={() => { if (window.confirm('Remove this plan?')) remove.mutate(p.plan_id); }}
                  className="px-3 py-1.5 text-xs rounded-lg border border-red-500/30 text-red-300 hover:bg-red-500/10">Remove</button>
              </div>
            </div>
          </div>
        )) : (
          <div className="card p-12 text-center text-gray-500 text-sm">No plans yet. Create one to offer shoppers a premium membership.</div>
        )}
      </div>
    </div>
  );
};
