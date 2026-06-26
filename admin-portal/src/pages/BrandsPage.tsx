import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api';

interface BrandInfo {
  brand_id: string;
  company_name: string;
  logo_url: string | null;
  product_count: number;
}

export const BrandsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Fetch Brands
  const { data: brands, isLoading, error } = useQuery<BrandInfo[]>({
    queryKey: ['brands', page],
    queryFn: async () => {
      const res = await api.get(`/admin/brands?page=${page}&page_size=${pageSize}`);
      return res.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-900/30 border border-red-500 text-red-200 rounded-md">
        Failed to load brands list.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Brand Partners</h1>
        <p className="text-gray-400 text-sm mt-1">View registered brand partners and their product inventory</p>
      </div>

      {/* Brands Table */}
      <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700/50">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-750">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider w-24">Logo</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Company Name</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Brand ID</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Active Products</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 bg-gray-800">
              {brands && brands.length > 0 ? (
                brands.map((brand) => (
                  <tr key={brand.brand_id} className="hover:bg-gray-750/30">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {brand.logo_url ? (
                        <img
                          src={brand.logo_url}
                          alt={`${brand.company_name} logo`}
                          className="w-10 h-10 object-contain rounded bg-gray-700 p-1 border border-gray-600"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded bg-gray-700 flex items-center justify-center text-lg font-bold text-blue-400 border border-gray-600">
                          {brand.company_name.charAt(0).toUpperCase()}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-white">
                      {brand.company_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400 font-mono">
                      {brand.brand_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-3 py-1 bg-blue-500/10 text-blue-400 rounded font-bold border border-blue-500/20">
                        {brand.product_count} products
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-gray-500 text-sm">
                    No brand partners registered yet.
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
            disabled={!brands || brands.length < pageSize}
            className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
