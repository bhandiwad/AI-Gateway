import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Layers, 
  Key, 
  Users, 
  Settings,
  LogOut,
  X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/playground', label: 'Playground', icon: MessageSquare },
  { path: '/models', label: 'Models', icon: Layers },
  { path: '/api-keys', label: 'API Keys', icon: Key },
  { path: '/tenants', label: 'Tenants', icon: Users, adminOnly: true },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ onNavClick }) {
  const location = useLocation();
  const { user, logout } = useAuth();

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
