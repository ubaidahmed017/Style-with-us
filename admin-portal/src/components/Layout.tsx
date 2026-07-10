import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

type NavItem = { to: string; label: string; icon: React.ReactNode };

const icon = (path: string) => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
    strokeWidth={1.8} stroke="currentColor" className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d={path} />
  </svg>
);

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: icon('M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z') },
  { to: '/users', label: 'Users', icon: icon('M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z') },
  { to: '/brands', label: 'Brands', icon: icon('M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 003.75.614m-16.5 0a3.004 3.004 0 01-.621-4.72L4.318 3.44A1.5 1.5 0 015.378 3h13.243a1.5 1.5 0 011.06.44l1.19 1.189a3 3 0 01-.621 4.72m-13.5 8.65h3.75a.75.75 0 00.75-.75V13.5a.75.75 0 00-.75-.75H6.75a.75.75 0 00-.75.75v3.75c0 .415.336.75.75.75z') },
  { to: '/finance', label: 'Finance', icon: icon('M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z') },
  { to: '/reports', label: 'Reports', icon: icon('M3 3v1.5M3 21v-6m0 0l2.77-.693a9 9 0 016.208.682l.108.054a9 9 0 006.086.71l3.114-.732a48.524 48.524 0 01-.005-10.499l-3.11.732a9 9 0 01-6.085-.711l-.108-.054a9 9 0 00-6.208-.682L3 4.5M3 15V4.5') },
  { to: '/plans', label: 'Plans', icon: icon('M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z') },
  { to: '/ml-jobs', label: 'ML Jobs', icon: icon('M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z') },
];

const Brand: React.FC = () => (
  <Link to="/" className="flex items-center gap-3">
    <img src="/admin/logo.svg" alt="" className="w-9 h-9 rounded-xl shadow-glow" />
    <div className="leading-tight">
      <div className="font-extrabold tracking-tight">Style With Us</div>
      <div className="text-[11px] font-semibold text-brand-300 uppercase tracking-widest">
        Admin
      </div>
    </div>
  </Link>
);

export const Layout: React.FC = () => {
  const { profile, logout } = useAuth();
  const location = useLocation();
  const active = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
  const current = NAV.find((n) => active(n.to))?.label ?? 'Dashboard';

  return (
    <div className="min-h-screen md:flex">
      {/* Sidebar (desktop) */}
      <aside className="hidden md:flex md:flex-col md:w-64 md:shrink-0 md:h-screen md:sticky md:top-0
        border-r border-white/10 bg-ink-800/60 backdrop-blur-xl p-4">
        <div className="px-2 py-3">
          <Brand />
        </div>
        <nav className="mt-6 space-y-1.5">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to}
              className={`nav-link ${active(n.to) ? 'nav-link-active' : ''}`}>
              {n.icon}
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="mt-auto">
          <div className="card p-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-brand-gradient grid place-items-center font-bold">
              {(profile?.name || profile?.email || 'A')[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold truncate">
                {profile?.name || 'Administrator'}
              </div>
              <div className="text-xs text-gray-400 truncate">{profile?.email}</div>
            </div>
          </div>
          <button onClick={logout} className="btn-ghost w-full mt-3">
            {icon('M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75')}
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden sticky top-0 z-20 flex items-center justify-between
        border-b border-white/10 bg-ink-800/80 backdrop-blur-xl px-4 py-3">
        <Brand />
        <button onClick={logout} className="btn-ghost px-3 py-2">Sign Out</button>
      </div>
      <nav className="md:hidden flex gap-2 overflow-x-auto px-4 py-3 border-b border-white/10">
        {NAV.map((n) => (
          <Link key={n.to} to={n.to}
            className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-medium
              ${active(n.to) ? 'bg-brand-gradient text-white' : 'bg-white/5 text-gray-300'}`}>
            {n.label}
          </Link>
        ))}
      </nav>

      {/* Main content */}
      <main className="flex-1 min-w-0">
        <header className="hidden md:flex items-center justify-between px-8 py-6
          border-b border-white/10">
          <h1 className="text-2xl font-bold">{current}</h1>
          <span className="text-xs text-gray-400">Live · auto-refresh 30s</span>
        </header>
        <div className="p-5 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
