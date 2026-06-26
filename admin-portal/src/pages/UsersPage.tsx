import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

interface UserResponse {
  user_id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export const UsersPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const queryClient = useQueryClient();
  const pageSize = 15;

  // Fetch Users
  const { data: users, isLoading, error } = useQuery<UserResponse[]>({
    queryKey: ['users', page, roleFilter],
    queryFn: async () => {
      const roleQuery = roleFilter ? `&role=${roleFilter}` : '';
      const res = await api.get(`/admin/users?page=${page}&page_size=${pageSize}${roleQuery}`);
      return res.data;
    },
  });

  // Mutation to update user role
  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, newRole }: { userId: string; newRole: string }) => {
      const res = await api.patch(`/admin/users/${userId}?new_role=${newRole}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('User role updated successfully.');
    },
    onError: (err: any) => {
      console.error('Error updating user role:', err);
      alert(err.response?.data?.detail || 'Failed to update user role.');
    },
  });

  const handleRoleChange = (userId: string, currentRole: string, newRole: string) => {
    if (currentRole === newRole) return;

    const confirmChange = window.confirm(
      `Are you sure you want to change this user's role from ${currentRole.toUpperCase()} to ${newRole.toUpperCase()}?`
    );

    if (confirmChange) {
      updateRoleMutation.mutate({ userId, newRole });
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

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
        Failed to load users list.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">User Management</h1>
          <p className="text-gray-400 text-sm mt-1">View registered accounts and assign roles</p>
        </div>

        {/* Filter Dropdown */}
        <div className="flex items-center space-x-2">
          <label htmlFor="role-filter" className="text-sm font-semibold text-gray-300">
            Filter by Role:
          </label>
          <select
            id="role-filter"
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1); // Reset to first page
            }}
            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Roles</option>
            <option value="shopper">Shopper</option>
            <option value="brand">Brand</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden border border-gray-700/50">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead className="bg-gray-750">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Joined</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 bg-gray-800">
              {users && users.length > 0 ? (
                users.map((user) => (
                  <tr key={user.user_id} className="hover:bg-gray-750/30">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{user.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{user.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                        user.role === 'admin' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        user.role === 'brand' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.user_id, user.role, e.target.value)}
                        className="bg-gray-700 border border-gray-600 rounded text-white text-xs py-1 px-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="shopper">Set Shopper</option>
                        <option value="brand">Set Brand</option>
                        <option value="admin">Set Admin</option>
                      </select>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500 text-sm">
                    No users found matching the selected criteria.
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
            disabled={!users || users.length < pageSize}
            className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-650 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
