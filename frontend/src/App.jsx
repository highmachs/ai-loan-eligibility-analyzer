import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CustomerForm from './pages/CustomerForm';
import PredictionResult from './pages/PredictionResult';
import AdminReports from './pages/AdminReports';
import DocumentManager from './pages/DocumentManager';
import AuditLog from './pages/AuditLog';
import UserManagement from './pages/UserManagement';
import CustomerHistory from './pages/CustomerHistory';

function isTokenValid() {
  const token = localStorage.getItem('token');
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

function EscapeKeyNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (location.pathname === '/login' || location.pathname === '/dashboard') return;

        if (location.pathname === '/admin/audit-logs' || location.pathname === '/admin/users') {
          navigate('/admin');
          return;
        }

        if (window.history.length > 2) {
          navigate(-1);
        } else {
          navigate('/dashboard');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [location.pathname, navigate]);

  return null;
}

function PrivateRoute({ children }) {
  if (!isTokenValid()) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AdminRoute({ children }) {
  if (!isTokenValid()) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return <Navigate to="/login" replace />;
  }
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  // ADMIN and SENIOR_CREDIT_MANAGER can access reports/admin views
  const canAccess = user.role === 'ADMIN' || user.role === 'SENIOR_CREDIT_MANAGER';
  if (!canAccess) return <Navigate to="/dashboard" replace />;
  return children;
}

// Strictly ADMIN-only (user management, audit logs)
function StrictAdminRoute({ children }) {
  if (!isTokenValid()) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return <Navigate to="/login" replace />;
  }
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  if (user.role !== 'ADMIN') return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <EscapeKeyNavigation />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/customers/new" element={<PrivateRoute><CustomerForm /></PrivateRoute>} />
        <Route path="/customers/:customerId/history" element={<PrivateRoute><CustomerHistory /></PrivateRoute>} />
        <Route path="/prediction/:loanId" element={<PrivateRoute><PredictionResult /></PrivateRoute>} />
        <Route path="/documents/:customerId" element={<PrivateRoute><DocumentManager /></PrivateRoute>} />
        <Route path="/admin" element={<AdminRoute><AdminReports /></AdminRoute>} />
        <Route path="/admin/audit-logs" element={<StrictAdminRoute><AuditLog /></StrictAdminRoute>} />
        <Route path="/admin/users" element={<StrictAdminRoute><UserManagement /></StrictAdminRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
