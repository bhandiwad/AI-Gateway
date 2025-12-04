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
  GitBranch,
  Building2,
  Bell
} from 'lucide-react';
import { useAuth, PERMISSIONS } from '../contexts/AuthContext';
import InfinitAILogo from './InfinitAILogo';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, permission: PERMISSIONS.DASHBOARD_VIEW },
  { path: '/router', label: 'Router', icon: GitBranch, permission: PERMISSIONS.ROUTER_VIEW },
  { path: '/models', label: 'Models', icon: Layers, permission: PERMISSIONS.DASHBOARD_VIEW },
  { path: '/playground', label: 'Playground', icon: MessageSquare, permission: PERMISSIONS.GATEWAY_USE },
  { path: '/guardrails', label: 'Guardrails', icon: Shield, permission: PERMISSIONS.GUARDRAILS_VIEW },
  { path: '/api-keys', label: 'API Keys', icon: Key, permission: PERMISSIONS.API_KEYS_VIEW },
  { path: '/users', label: 'Users', icon: Users, permission: PERMISSIONS.USERS_VIEW },
  { path: '/organization', label: 'Organization', icon: Building2, permission: PERMISSIONS.USERS_VIEW },
  { path: '/alerts', label: 'Alerts', icon: Bell, permission: PERMISSIONS.SETTINGS_VIEW },
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
    <div className="flex flex-col h-full bg-white text-gray-800 w-64 md:w-64 border-r border-gray-200">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <InfinitAILogo className="w-10 h-10" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">InfinitAI</h1>
            <p className="text-xs text-gray-500">AI Gateway</p>
          </div>
        </div>
        <button
          onClick={onNavClick}
          className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors text-gray-600"
          aria-label="Close menu"
        >
          <X size={20} />
        </button>
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
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
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all min-h-[44px] ${
                    isActive 
                      ? 'bg-lime-100 text-lime-800 font-medium' 
                      : 'text-gray-600 hover:bg-gray-100 active:bg-gray-200'
                  }`}
                >
                  <div className={`p-1.5 rounded-lg ${isActive ? 'bg-lime-200' : 'bg-gray-100'}`}>
                    <Icon size={18} className={isActive ? 'text-lime-700' : 'text-gray-500'} />
                  </div>
                  <span className="text-sm">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 mb-4 p-2 bg-gray-50 rounded-xl">
          <div className="w-10 h-10 bg-gradient-to-br from-lime-400 to-green-500 rounded-full flex items-center justify-center flex-shrink-0 text-white font-semibold">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            {role && (
              <span className={`text-xs px-2 py-0.5 rounded mt-1 inline-block ${
                role === 'admin' ? 'bg-lime-100 text-lime-700' :
                role === 'manager' ? 'bg-green-100 text-green-700' :
                role === 'user' ? 'bg-emerald-100 text-emerald-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {role.charAt(0).toUpperCase() + role.slice(1)}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-4 py-3 text-sm text-gray-600 hover:bg-gray-100 active:bg-gray-200 rounded-xl transition-colors min-h-[44px]"
        >
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
