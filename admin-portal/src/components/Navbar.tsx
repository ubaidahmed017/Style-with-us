import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { profile, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path
      ? 'bg-blue-600 text-white'
      : 'text-gray-300 hover:bg-gray-700 hover:text-white';
  };

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl mr-2">👗</span>
              <span className="font-bold text-xl text-white tracking-wider">Style With Us</span>
              <span className="ml-2 px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs font-semibold rounded border border-blue-500/30">
                Admin
              </span>
            </Link>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  to="/"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/')}`}
                >
                  Dashboard
                </Link>
                <Link
                  to="/users"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/users')}`}
                >
                  Users
                </Link>
                <Link
                  to="/brands"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/brands')}`}
                >
                  Brands
                </Link>
                <Link
                  to="/ml-jobs"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/ml-jobs')}`}
                >
                  ML Jobs
                </Link>
              </div>
            </div>
          </div>
          <div className="flex items-center">
            <div className="hidden md:flex items-center mr-4">
              <div className="text-right">
                <div className="text-sm font-semibold text-white">{profile?.name || 'Administrator'}</div>
                <div className="text-xs text-gray-400">{profile?.email}</div>
              </div>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Mobile navigation */}
      <div className="md:hidden border-t border-gray-700 bg-gray-800/50">
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 flex justify-around">
          <Link
            to="/"
            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/')}`}
          >
            Dashboard
          </Link>
          <Link
            to="/users"
            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/users')}`}
          >
            Users
          </Link>
          <Link
            to="/brands"
            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/brands')}`}
          >
            Brands
          </Link>
          <Link
            to="/ml-jobs"
            className={`block px-3 py-2 rounded-md text-base font-medium ${isActive('/ml-jobs')}`}
          >
            ML Jobs
          </Link>
        </div>
      </div>
    </nav>
  );
};
