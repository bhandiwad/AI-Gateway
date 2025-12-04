import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Layers, 
  Key, 
  Users, 
  Settings,
  LogOut,
  X,
  FileText,
  DollarSign,
  Shield,
  ShieldCheck,
  GitBranch,
  Building2,
  Activity
} from 'lucide-react';
import { useAuth, PERMISSIONS } from '../contexts/AuthContext';

import { Bell } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, permission: PERMISSIONS.DASHBOARD_VIEW },
  { path: '/health', label: 'Health & Reliability', icon: Activity, permission: PERMISSIONS.ROUTER_VIEW },
  { path: '/alerts', label: 'Alerts', icon: Bell, permission: PERMISSIONS.SETTINGS_VIEW },
  { path: '/router', label: 'Router', icon: GitBranch, permission: PERMISSIONS.ROUTER_VIEW },
  { path: '/models', label: 'Models', icon: Layers, permission: PERMISSIONS.DASHBOARD_VIEW },
  { path: '/playground', label: 'Playground', icon: MessageSquare, permission: PERMISSIONS.GATEWAY_USE },
  { path: '/guardrails', label: 'Guardrails', icon: Shield, permission: PERMISSIONS.GUARDRAILS_VIEW },
  { path: '/external-guardrails', label: 'External Guardrails', icon: ShieldCheck, permission: PERMISSIONS.GUARDRAILS_VIEW },
  { path: '/api-keys', label: 'API Keys', icon: Key, permission: PERMISSIONS.API_KEYS_VIEW },
  { path: '/users', label: 'Users', icon: Users, permission: PERMISSIONS.USERS_VIEW },
  { path: '/organization', label: 'Organization', icon: Building2, permission: PERMISSIONS.USERS_VIEW },
  { path: '/billing', label: 'Billing', icon: DollarSign, permission: PERMISSIONS.BILLING_VIEW },
  { path: '/audit-logs', label: 'Audit Logs', icon: FileText, permission: PERMISSIONS.AUDIT_VIEW },
  { path: '/tenants', label: 'Tenants', icon: Building2, adminOnly: true },
  { path: '/settings', label: 'Settings', icon: Settings, permission: PERMISSIONS.SETTINGS_VIEW },
];

export default function Sidebar({ onNavClick }) {
  const location = useLocation();
  const { user, logout, hasPermission, role } = useAuth();

  const handleNavClick = () => {
    if (onNavClick) {
      onNavClick();
    }
  };

  const handleLogout = () => {
    handleNavClick();
    logout();
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white w-64 md:w-64">
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">AI Gateway</h1>
          <p className="text-sm text-gray-400 mt-1">Enterprise Platform</p>
        </div>
        <button
          onClick={onNavClick}
          className="md:hidden p-2 rounded-lg hover:bg-gray-800 transition-colors"
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      </div>

      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {navItems.map((item) => {
            if (item.adminOnly && !user?.is_admin) return null;
            if (item.permission && !hasPermission(item.permission)) return null;
            
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={handleNavClick}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors min-h-[44px] ${
                    isActive 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:bg-gray-800 active:bg-gray-700'
                  }`}
                >
                  <Icon size={20} />
                  <span className="text-base">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            {role && (
              <span className={`text-xs px-2 py-0.5 rounded mt-1 inline-block ${
                role === 'admin' ? 'bg-purple-600 text-purple-100' :
                role === 'manager' ? 'bg-blue-600 text-blue-100' :
                role === 'user' ? 'bg-green-600 text-green-100' :
                'bg-gray-600 text-gray-100'
              }`}>
                {role.charAt(0).toUpperCase() + role.slice(1)}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-4 py-3 text-sm text-gray-300 hover:bg-gray-800 active:bg-gray-700 rounded-lg transition-colors min-h-[44px]"
        >
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
