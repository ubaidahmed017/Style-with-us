import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { UsersPage } from './pages/UsersPage';
import { BrandsPage } from './pages/BrandsPage';
import { MLJobsPage } from './pages/MLJobsPage';
import { ReportsPage } from './pages/ReportsPage';
import { FinancePage } from './pages/FinancePage';
import { PlansPage } from './pages/PlansPage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Admin Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/brands" element={<BrandsPage />} />
                <Route path="/finance" element={<FinancePage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/plans" element={<PlansPage />} />
                <Route path="/ml-jobs" element={<MLJobsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
