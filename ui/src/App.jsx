import { useState, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import InfinitAILogo from './components/InfinitAILogo';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Models from './pages/Models';
import PlaygroundPage from './pages/PlaygroundPage';
import ApiKeys from './pages/ApiKeys';
import Tenants from './pages/Tenants';
import Settings from './pages/Settings';
import AuditLogs from './pages/AuditLogs';
import Billing from './pages/Billing';
import Guardrails from './pages/Guardrails';
import RouterConfig from './pages/RouterConfig';
import Users from './pages/Users';
import Organization from './pages/Organization';
import Alerts from './pages/Alerts';
import { Menu, X } from 'lucide-react';

const MobileMenuContext = createContext();

export function useMobileMenu() {
  return useContext(MobileMenuContext);
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <InfinitAILogo className="w-16 h-16 animate-pulse" />
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lime-600"></div>
        </div>
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
}

function AppLayout({ children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <MobileMenuContext.Provider value={{ mobileMenuOpen, setMobileMenuOpen }}>
      <div className="flex flex-col md:flex-row h-screen bg-gray-100">
        <div className="md:hidden bg-white text-gray-800 px-4 py-3 flex items-center justify-between border-b border-gray-200">
          <div className="flex items-center gap-3">
            <InfinitAILogo className="w-8 h-8" />
            <div>
              <h1 className="text-lg font-bold text-gray-900">InfinitAI</h1>
              <p className="text-xs text-gray-500">AI Gateway</p>
            </div>
          </div>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        <div className={`
          fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <Sidebar onNavClick={() => setMobileMenuOpen(false)} />
        </div>

        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </MobileMenuContext.Provider>
  );
}

function AppRoutes() {
  const { user } = useAuth();
  
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />
      
      <Route path="/" element={
        <PrivateRoute>
          <AppLayout>
            <Dashboard />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/playground" element={
        <PrivateRoute>
          <AppLayout>
            <PlaygroundPage />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/models" element={
        <PrivateRoute>
          <AppLayout>
            <Models />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/api-keys" element={
        <PrivateRoute>
          <AppLayout>
            <ApiKeys />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/tenants" element={
        <PrivateRoute>
          <AppLayout>
            <Tenants />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/settings" element={
        <PrivateRoute>
          <AppLayout>
            <Settings />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/audit-logs" element={
        <PrivateRoute>
          <AppLayout>
            <AuditLogs />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/billing" element={
        <PrivateRoute>
          <AppLayout>
            <Billing />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/guardrails" element={
        <PrivateRoute>
          <AppLayout>
            <Guardrails />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/router" element={
        <PrivateRoute>
          <AppLayout>
            <RouterConfig />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/users" element={
        <PrivateRoute>
          <AppLayout>
            <Users />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/organization" element={
        <PrivateRoute>
          <AppLayout>
            <Organization />
          </AppLayout>
        </PrivateRoute>
      } />
      
      <Route path="/alerts" element={
        <PrivateRoute>
          <AppLayout>
            <Alerts />
          </AppLayout>
        </PrivateRoute>
      } />

      {/* Redirect old routes */}
      <Route path="/health" element={<Navigate to="/" replace />} />
      <Route path="/external-guardrails" element={<Navigate to="/guardrails" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
