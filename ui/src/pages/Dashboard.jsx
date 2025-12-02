import { useState, useEffect } from 'react';
import { usageApi } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import UsageChart from '../components/UsageChart';
import { Activity, DollarSign, Clock, CheckCircle, TrendingUp, Zap } from 'lucide-react';

function StatCard({ icon: Icon, label, value, subvalue, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
      <div className="flex items-center gap-3 sm:gap-4">
        <div className={`p-2.5 sm:p-3 rounded-lg ${color} flex-shrink-0`}>
          <Icon className="text-white" size={20} />
        </div>
        <div className="min-w-0">
          <p className="text-xs sm:text-sm text-gray-500">{label}</p>
          <p className="text-lg sm:text-2xl font-bold text-gray-800 truncate">{value}</p>
          {subvalue && <p className="text-xs text-gray-400 truncate">{subvalue}</p>}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadStats();
  }, [days]);

  const loadStats = async () => {
    try {
      const response = await usageApi.dashboard(days);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toString() || '0';
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Dashboard" />
      
      <div className="flex-1 overflow-auto p-4 sm:p-6 bg-gray-50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
            Welcome back, {user?.name}
          </h1>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base min-h-[44px] w-full sm:w-auto"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-4 sm:mb-6">
              <StatCard
                icon={Activity}
                label="Total Requests"
                value={formatNumber(stats?.total_requests)}
                subvalue={stats?.period}
                color="bg-blue-500"
              />
              <StatCard
                icon={Zap}
                label="Total Tokens"
                value={formatNumber(stats?.total_tokens)}
                color="bg-purple-500"
              />
              <StatCard
                icon={DollarSign}
                label="Total Cost"
                value={`$${stats?.total_cost?.toFixed(2) || '0.00'}`}
                color="bg-green-500"
              />
              <StatCard
                icon={Clock}
                label="Avg Latency"
                value={`${stats?.avg_latency_ms?.toFixed(0) || 0}ms`}
                subvalue={`${stats?.success_rate?.toFixed(1) || 100}% success`}
                color="bg-orange-500"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
              <div className="lg:col-span-2">
                <UsageChart data={stats?.usage_over_time} />
              </div>
              
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-3 sm:mb-4">Top Models</h3>
                <div className="space-y-3 sm:space-y-4">
                  {stats?.top_models?.slice(0, 5).map((model, index) => (
                    <div key={model.model} className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                        <span className="text-xs sm:text-sm font-medium text-gray-500 flex-shrink-0">#{index + 1}</span>
                        <div className="min-w-0">
                          <p className="text-xs sm:text-sm font-medium text-gray-800 truncate">{model.model}</p>
                          <p className="text-xs text-gray-400 truncate">{model.provider}</p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs sm:text-sm font-medium text-gray-800">{formatNumber(model.requests)}</p>
                        <p className="text-xs text-gray-400">${model.cost?.toFixed(4)}</p>
                      </div>
                    </div>
                  ))}
                  {(!stats?.top_models || stats.top_models.length === 0) && (
                    <p className="text-sm text-gray-400 text-center py-4">No usage data yet</p>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-3 sm:mb-4">Account Status</h3>
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Status</span>
                    <span className="flex items-center gap-1 text-green-600 text-sm">
                      <CheckCircle size={16} />
                      Active
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Plan</span>
                    <span className="font-medium text-sm">{user?.is_admin ? 'Admin' : 'Standard'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Rate Limit</span>
                    <span className="font-medium text-sm">{user?.rate_limit} req/min</span>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-500">Budget Usage</span>
                      <span className="font-medium text-sm">
                        ${user?.current_spend?.toFixed(2)} / ${user?.monthly_budget?.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, (user?.current_spend / user?.monthly_budget) * 100)}%`
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-gray-800 mb-3 sm:mb-4">Quick Actions</h3>
                <div className="grid grid-cols-2 gap-2 sm:gap-3">
                  <a
                    href="/playground"
                    className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 active:bg-blue-200 transition-colors min-h-[48px] text-sm sm:text-base"
                  >
                    <TrendingUp size={18} />
                    <span>Playground</span>
                  </a>
                  <a
                    href="/api-keys"
                    className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 active:bg-green-200 transition-colors min-h-[48px] text-sm sm:text-base"
                  >
                    <Zap size={18} />
                    <span>API Keys</span>
                  </a>
                  <a
                    href="/models"
                    className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 active:bg-purple-200 transition-colors min-h-[48px] text-sm sm:text-base"
                  >
                    <Activity size={18} />
                    <span>Models</span>
                  </a>
                  <a
                    href="/settings"
                    className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 active:bg-orange-200 transition-colors min-h-[48px] text-sm sm:text-base"
                  >
                    <Clock size={18} />
                    <span>Settings</span>
                  </a>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
