import { Bell, Search } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Header({ title }) {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
      
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search..."
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <button className="relative p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        
        {user && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Budget:</span>
            <span className="font-medium">
              ${user.current_spend?.toFixed(2)} / ${user.monthly_budget?.toFixed(2)}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
