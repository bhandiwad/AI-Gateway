import { useState, useEffect } from 'react';
import { usageApi } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import UsageChart from '../components/UsageChart';
import { 
  Activity, DollarSign, Clock, CheckCircle, TrendingUp, Zap,
  AlertCircle, XCircle, RefreshCw, BarChart3, Heart
} from 'lucide-react';

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

function OverviewTab({ stats, loading, user, formatNumber, formatCurrency }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-lime-600"></div>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-4 sm:mb-6">
        <StatCard
          icon={Activity}
          label="Total Requests"
          value={formatNumber(stats?.total_requests)}
          subvalue={stats?.period}
          color="bg-lime-500"
        />
        <StatCard
          icon={Zap}
          label="Total Tokens"
          value={formatNumber(stats?.total_tokens)}
          color="bg-green-500"
        />
        <StatCard
          icon={DollarSign}
          label="Total Cost"
          value={formatCurrency(stats?.total_cost)}
          color="bg-emerald-500"
        />
        <StatCard
          icon={Clock}
          label="Avg Latency"
          value={`${stats?.avg_latency_ms?.toFixed(0) || 0}ms`}
          subvalue={`${stats?.success_rate?.toFixed(1) || 100}% success`}
          color="bg-teal-500"
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
                  <p className="text-xs text-gray-400">{formatCurrency(model.cost)}</p>
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
                  {formatCurrency(user?.current_spend)} / {formatCurrency(user?.monthly_budget)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-lime-500 h-2 rounded-full"
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
              className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-lime-50 text-lime-700 rounded-lg hover:bg-lime-100 active:bg-lime-200 transition-colors min-h-[48px] text-sm sm:text-base"
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
              className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 active:bg-emerald-200 transition-colors min-h-[48px] text-sm sm:text-base"
            >
              <Activity size={18} />
              <span>Models</span>
            </a>
            <a
              href="/settings"
              className="flex items-center justify-center gap-2 p-3 sm:p-4 bg-teal-50 text-teal-700 rounded-lg hover:bg-teal-100 active:bg-teal-200 transition-colors min-h-[48px] text-sm sm:text-base"
            >
              <Clock size={18} />
              <span>Settings</span>
            </a>
          </div>
        </div>
      </div>
    </>
  );
}

function HealthTab() {
  const [healthData, setHealthData] = useState(null);
  const [circuitBreakers, setCircuitBreakers] = useState({});
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealthData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const dashboardRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/health-dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const dashboard = await dashboardRes.json();
      setHealthData(dashboard);

      const cbRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const cb = await cbRes.json();
      setCircuitBreakers(cb);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching health data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    const interval = autoRefresh ? setInterval(fetchHealthData, 10000) : null;
    return () => interval && clearInterval(interval);
  }, [autoRefresh]);

  const getStateColor = (state) => {
    switch (state?.toLowerCase()) {
      case 'closed': return 'text-green-600 bg-green-100';
      case 'open': return 'text-red-600 bg-red-100';
      case 'half_open': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStateIcon = (state) => {
    switch (state?.toLowerCase()) {
      case 'closed': return <CheckCircle className="w-5 h-5" />;
      case 'open': return <XCircle className="w-5 h-5" />;
      case 'half_open': return <AlertCircle className="w-5 h-5" />;
      default: return <Clock className="w-5 h-5" />;
    }
  };

  const forceCircuitState = async (provider, action) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers/${provider}/force-${action}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      fetchHealthData();
    } catch (error) {
      console.error('Error updating circuit breaker:', error);
    }
  };

  const resetCircuitBreaker = async (provider) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers/${provider}/reset`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      fetchHealthData();
    } catch (error) {
      console.error('Error resetting circuit breaker:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-lime-600" />
      </div>
    );
  }

  const providers = healthData?.providers || [];
  const summary = circuitBreakers?.summary || {};

  return (
    <>
      <div className="flex justify-end mb-4">
        <div className="flex gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-lime-600 focus:ring-lime-500"
            />
            Auto-refresh (10s)
          </label>
          <button
            onClick={fetchHealthData}
            className="px-4 py-2 bg-lime-600 text-white rounded-lg hover:bg-lime-700 flex items-center gap-2 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 border-l-4 border-l-lime-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Providers</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total || 0}</p>
            </div>
            <Activity className="w-8 h-8 text-lime-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 border-l-4 border-l-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Healthy (Closed)</p>
              <p className="text-2xl font-bold text-green-600">{summary.closed || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 border-l-4 border-l-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Unhealthy (Open)</p>
              <p className="text-2xl font-bold text-red-600">{summary.open || 0}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 border-l-4 border-l-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Testing (Half-Open)</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.half_open || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {providers.map((provider) => {
          const circuitBreaker = provider.circuit_breaker || {};
          const groups = provider.groups || [];

          return (
            <div key={provider.name} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-lime-50 to-green-50 p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-gray-900">{provider.name}</h2>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1 ${getStateColor(circuitBreaker.state)}`}>
                      {getStateIcon(circuitBreaker.state)}
                      {circuitBreaker.state?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {circuitBreaker.state === 'open' && (
                      <button
                        onClick={() => forceCircuitState(provider.name, 'close')}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                      >
                        Force Close
                      </button>
                    )}
                    {circuitBreaker.state === 'closed' && (
                      <button
                        onClick={() => forceCircuitState(provider.name, 'open')}
                        className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
                      >
                        Force Open
                      </button>
                    )}
                    <button
                      onClick={() => resetCircuitBreaker(provider.name)}
                      className="px-3 py-1 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-4">
                {circuitBreaker && Object.keys(circuitBreaker).length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Circuit Breaker Metrics
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-600">Failures</p>
                        <p className="text-lg font-semibold text-red-600">{circuitBreaker.failure_count || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-600">Successes</p>
                        <p className="text-lg font-semibold text-green-600">{circuitBreaker.success_count || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-600">Consecutive Failures</p>
                        <p className="text-lg font-semibold text-orange-600">{circuitBreaker.consecutive_failures || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-600">Rejected Requests</p>
                        <p className="text-lg font-semibold text-red-600">{circuitBreaker.rejected_requests || 0}</p>
                      </div>
                    </div>
                  </div>
                )}

                {groups.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Load Balancer Groups ({groups.length})
                    </h3>
                    <div className="space-y-2">
                      {groups.map((group) => (
                        <div key={group.group} className="bg-gray-50 p-3 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">{group.group}</span>
                            <span className={`text-xs px-2 py-1 rounded-lg ${group.is_healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {group.is_healthy ? 'Healthy' : 'Unhealthy'}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                            <div>
                              <p className="text-xs text-gray-600">Weight</p>
                              <p className="font-semibold">{group.weight}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Active Requests</p>
                              <p className="font-semibold text-lime-600">{group.active_requests}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Total Requests</p>
                              <p className="font-semibold">{group.total_requests}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Avg Latency</p>
                              <p className="font-semibold text-green-600">{group.avg_latency_ms?.toFixed(0) || 0}ms</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {groups.length === 0 && (!circuitBreaker || Object.keys(circuitBreaker).length === 0) && (
                  <p className="text-gray-500 text-sm italic">No metrics available for this provider</p>
                )}
              </div>
            </div>
          );
        })}

        {providers.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Providers Configured</h3>
            <p className="text-gray-600">Configure providers to start monitoring health and performance.</p>
          </div>
        )}
      </div>
    </>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [activeTab, setActiveTab] = useState('overview');

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

  const USD_TO_INR = 83.5;
  
  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toString() || '0';
  };

  const formatCurrency = (amount) => {
    const inrAmount = (amount || 0) * USD_TO_INR;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(inrAmount);
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'health', label: 'Health & Reliability', icon: Heart },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Dashboard" />
      
      <div className="flex-1 overflow-auto p-4 sm:p-6 bg-gray-50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
            Welcome back, {user?.name}
          </h1>
          {activeTab === 'overview' && (
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lime-500 text-sm sm:text-base min-h-[44px] w-full sm:w-auto"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          )}
        </div>

        <div className="flex gap-2 mb-6 border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-lime-500 text-lime-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {activeTab === 'overview' ? (
          <OverviewTab
            stats={stats}
            loading={loading}
            user={user}
            formatNumber={formatNumber}
            formatCurrency={formatCurrency}
          />
        ) : (
          <HealthTab />
        )}
      </div>
    </div>
  );
}
