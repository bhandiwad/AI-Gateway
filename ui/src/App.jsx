import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Models from './pages/Models';
import PlaygroundPage from './pages/PlaygroundPage';
import ApiKeys from './pages/ApiKeys';
import Tenants from './pages/Tenants';
import Settings from './pages/Settings';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
}

function AppLayout({ children }) {
  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
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
