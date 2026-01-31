import { Bell, Search } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Header({ title }) {
  const { user } = useAuth();

  return (
    <header className="h-14 sm:h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 sm:px-6">
      <h2 className="text-lg sm:text-xl font-semibold text-gray-800 truncate">{title}</h2>
      
      <div className="flex items-center gap-2 sm:gap-4">
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search..."
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-48 lg:w-64"
          />
        </div>
        
        <button className="relative p-2.5 text-gray-500 hover:bg-gray-100 active:bg-gray-200 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        
        {user && user.monthly_budget > 0 && (
          <div className="hidden sm:flex items-center gap-2 text-sm">
            <span className="text-gray-500">Budget:</span>
            <span className="font-medium">
              ₹{((user.current_spend || 0) * 83.5).toLocaleString('en-IN', {maximumFractionDigits: 0})} / ₹{(user.monthly_budget * 83.5).toLocaleString('en-IN', {maximumFractionDigits: 0})}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
