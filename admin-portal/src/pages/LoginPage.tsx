import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from '../firebase';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { currentUser, isAdmin, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading && currentUser && isAdmin) {
      navigate('/', { replace: true });
    }
  }, [currentUser, isAdmin, authLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err: any) {
      console.error('Login error:', err);
      let msg = 'Failed to sign in. Please check your credentials.';
      if (err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password') {
        msg = 'Incorrect email or password.';
      } else if (err.code === 'auth/invalid-email') {
        msg = 'Invalid email address.';
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const showNotAdminError = currentUser && !isAdmin && !authLoading;

  return (
    <div className="flex items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <img src="/admin/logo.svg" alt="" className="w-16 h-16 rounded-2xl shadow-glow" />
          <h1 className="text-2xl font-extrabold tracking-tight mt-4">Style With Us</h1>
          <p className="text-gray-400 mt-1 text-sm">Administrator Portal</p>
        </div>

        <div className="card p-8">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/40 text-red-300 text-sm">
              {error}
            </div>
          )}
          {showNotAdminError && (
            <div className="mb-5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-300 text-sm">
              Signed in, but this account lacks administrator privileges.
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1.5">
                Email
              </label>
              <input
                id="email" type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="field" placeholder="admin@stylewithus.com" disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1.5">
                Password
              </label>
              <input
                id="password" type="password" required value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="field" placeholder="••••••••" disabled={loading}
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>
        <p className="text-center text-xs text-gray-500 mt-6">
          Restricted to authorized administrators.
        </p>
      </div>
    </div>
  );
};
