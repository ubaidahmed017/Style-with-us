import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute: React.FC = () => {
  const { currentUser, isAdmin, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-white">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-400 font-medium">Verifying credentials...</p>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-white p-6">
        <div className="max-w-md w-full card p-8 text-center">
          <div className="w-16 h-16 bg-red-900/50 border border-red-500 rounded-full flex items-center justify-center mx-auto mb-6 text-red-500">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-red-400 mb-2">Access Denied</h1>
          <p className="text-gray-400 mb-6">
            Your account does not have administrator privileges. This portal is restricted to authorized admins only.
          </p>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => window.location.href = '/'}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-white font-medium transition"
            >
              Back to Home
            </button>
            <button
              onClick={logout}
              className="text-red-400 hover:text-red-300 font-medium text-sm transition"
            >
              Log Out and Switch Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <Outlet />;
};
