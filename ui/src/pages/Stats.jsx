import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import Header from '../components/Header';
import { 
  BarChart3, Database, Trash2, RefreshCw, Clock, Zap, 
  TrendingUp, Activity, AlertCircle, CheckCircle, Settings,
  HardDrive, Cpu, Users, FileText, Key, Building2, Layers
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const USD_TO_INR = 83.5;
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

function StatCard({ icon: Icon, label, value, subvalue, color, trend }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="text-white" size={22} />
        </div>
        {trend && (
          <span className={`text-sm font-medium ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
        {subvalue && <p className="text-xs text-gray-400 mt-1">{subvalue}</p>}
      </div>
    </div>
  );
}

function DataTable({ title, icon: Icon, columns, data, emptyMessage }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Icon size={20} className="text-gray-400" />
          <h3 className="font-semibold text-gray-900">{title}</h3>
        </div>
        <p className="text-gray-400 text-center py-8">{emptyMessage || 'No data available'}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center gap-2 p-4 border-b border-gray-100">
        <Icon size={20} className="text-gray-400" />
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className="px-4 py-3 text-sm text-gray-900">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Stats() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [cacheStats, setCacheStats] = useState(null);
  const [detailedStats, setDetailedStats] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadStats();
  }, [days]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [cacheRes, detailedRes] = await Promise.all([
        api.get('/admin/cache/stats', { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: null })),
        api.get(`/admin/stats/detailed?days=${days}`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: null }))
      ]);
      setCacheStats(cacheRes.data);
      setDetailedStats(detailedRes.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
      setError('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const clearCache = async () => {
    if (!confirm('Are you sure you want to clear the entire cache? This action cannot be undone.')) {
      return;
    }

    try {
      setClearing(true);
      await api.delete('/admin/cache/clear', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Cache cleared successfully');
      loadStats();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to clear cache');
      setTimeout(() => setError(null), 3000);
    } finally {
      setClearing(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num?.toLocaleString('en-IN') || '0';
  };

  const formatINR = (amountUSD) => {
    const inr = (amountUSD || 0) * USD_TO_INR;
    return `₹${inr.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const summary = detailedStats?.summary || {};
  const topModels = detailedStats?.top_models || [];
  const byApiKey = detailedStats?.by_api_key || [];
  const byUser = detailedStats?.by_user || [];
  const byDepartment = detailedStats?.by_department || [];
  const hourlyDist = detailedStats?.hourly_distribution || [];
  const errorBreakdown = detailedStats?.error_breakdown || {};

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'models', label: 'Models', icon: Layers },
    { id: 'apikeys', label: 'API Keys', icon: Key },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'departments', label: 'Departments', icon: Building2 },
    { id: 'cache', label: 'Cache', icon: Database },
    { id: 'performance', label: 'Performance', icon: Cpu },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Statistics & Cache Management" />
      
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
              <AlertCircle className="text-red-500" size={20} />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
              <CheckCircle className="text-green-500" size={20} />
              <span className="text-green-700">{success}</span>
            </div>
          )}

          <div className="flex gap-2 mb-6 border-b border-gray-200">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Icon size={18} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {activeTab === 'cache' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Prompt Cache</h2>
                  <p className="text-sm text-gray-500">Semantic caching reduces API costs by reusing similar responses</p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={loadStats}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-medium"
                  >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    Refresh
                  </button>
                  <button
                    onClick={clearCache}
                    disabled={clearing || !cacheStats?.enabled}
                    className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium disabled:opacity-50"
                  >
                    <Trash2 size={16} />
                    {clearing ? 'Clearing...' : 'Clear Cache'}
                  </button>
                </div>
              </div>

              {!cacheStats?.enabled ? (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
                  <AlertCircle className="mx-auto text-amber-500 mb-3" size={40} />
                  <h3 className="font-semibold text-gray-900 mb-2">Semantic Cache Disabled</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Enable ENABLE_SEMANTIC_CACHE=true in your environment to use prompt caching.
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                      icon={Zap}
                      label="Cache Hits"
                      value={formatNumber(cacheStats?.hits || 0)}
                      subvalue={`${cacheStats?.hit_rate || 0}% hit rate`}
                      color="bg-green-500"
                    />
                    <StatCard
                      icon={Activity}
                      label="Cache Misses"
                      value={formatNumber(cacheStats?.misses || 0)}
                      color="bg-blue-500"
                    />
                    <StatCard
                      icon={TrendingUp}
                      label="Tokens Saved"
                      value={formatNumber(cacheStats?.tokens_saved || 0)}
                      subvalue="Estimated from cache hits"
                      color="bg-purple-500"
                    />
                    <StatCard
                      icon={Database}
                      label="Cost Saved"
                      value={`₹${(cacheStats?.cost_saved_inr || 0).toLocaleString('en-IN')}`}
                      subvalue={`$${(cacheStats?.cost_saved_usd || 0).toFixed(4)} USD`}
                      color="bg-emerald-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white rounded-xl border border-gray-200 p-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Cache Configuration</h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <div className="flex items-center gap-3">
                            <Clock size={18} className="text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900">TTL (Time to Live)</p>
                              <p className="text-sm text-gray-500">How long entries are cached</p>
                            </div>
                          </div>
                          <span className="font-mono text-sm bg-gray-100 px-3 py-1 rounded">1 hour</span>
                        </div>
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <div className="flex items-center gap-3">
                            <HardDrive size={18} className="text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900">Max Cache Size</p>
                              <p className="text-sm text-gray-500">Maximum entries in cache</p>
                            </div>
                          </div>
                          <span className="font-mono text-sm bg-gray-100 px-3 py-1 rounded">10,000</span>
                        </div>
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <div className="flex items-center gap-3">
                            <Settings size={18} className="text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900">Similarity Threshold</p>
                              <p className="text-sm text-gray-500">Minimum match score for semantic hits</p>
                            </div>
                          </div>
                          <span className="font-mono text-sm bg-gray-100 px-3 py-1 rounded">92%</span>
                        </div>
                        <div className="flex items-center justify-between py-3">
                          <div className="flex items-center gap-3">
                            <Database size={18} className="text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900">Current Cache Size</p>
                              <p className="text-sm text-gray-500">Entries currently cached</p>
                            </div>
                          </div>
                          <span className="font-mono text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded">
                            {formatNumber(cacheStats?.cache_size || 0)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-xl border border-gray-200 p-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Cache Details</h3>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <span className="text-gray-600">Embeddings Indexed</span>
                          <span className="font-medium">{formatNumber(cacheStats?.embeddings_indexed || 0)}</span>
                        </div>
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <span className="text-gray-600">Tenants Cached</span>
                          <span className="font-medium">{cacheStats?.tenants_cached || 0}</span>
                        </div>
                        <div className="flex items-center justify-between py-3 border-b border-gray-100">
                          <span className="text-gray-600">Evictions</span>
                          <span className="font-medium">{formatNumber(cacheStats?.evictions || 0)}</span>
                        </div>
                        <div className="flex items-center justify-between py-3">
                          <span className="text-gray-600">Cache Status</span>
                          <span className="flex items-center gap-2 text-green-600 font-medium">
                            <CheckCircle size={16} />
                            Active
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-900">Overview</h2>
                <select
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={Activity}
                  label="Total Requests"
                  value={formatNumber(summary?.total_requests || 0)}
                  subvalue={`Last ${days} days`}
                  color="bg-blue-500"
                />
                <StatCard
                  icon={Zap}
                  label="Total Tokens"
                  value={formatNumber(summary?.total_tokens || 0)}
                  color="bg-green-500"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Total Cost"
                  value={formatINR(summary?.total_cost || 0)}
                  color="bg-emerald-500"
                />
                <StatCard
                  icon={Clock}
                  label="Avg Latency"
                  value={`${(summary?.avg_latency_ms || 0).toFixed(0)}ms`}
                  subvalue={`${(summary?.success_rate || 100).toFixed(1)}% success`}
                  color="bg-purple-500"
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Request Distribution by Hour</h3>
                  <div className="h-64">
                    {hourlyDist.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={hourlyDist}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="hour" tickFormatter={(h) => `${h}:00`} />
                          <YAxis />
                          <Tooltip labelFormatter={(h) => `${h}:00 - ${h}:59`} />
                          <Bar dataKey="requests" fill="#3b82f6" name="Requests" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-gray-400 text-center py-16">No hourly data available</p>
                    )}
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Error Breakdown</h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-4 bg-green-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-green-700">{formatNumber(errorBreakdown?.success || 0)}</p>
                      <p className="text-sm text-green-600">Successful</p>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-red-700">{formatNumber(errorBreakdown?.errors || 0)}</p>
                      <p className="text-sm text-red-600">Errors</p>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-blue-700">{formatNumber(errorBreakdown?.cache_hits || 0)}</p>
                      <p className="text-sm text-blue-600">Cache Hits</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <p className="text-2xl font-bold text-gray-700">{formatNumber(errorBreakdown?.total_requests || 0)}</p>
                      <p className="text-sm text-gray-600">Total</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'models' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-900">Model Usage</h2>
              <DataTable
                title="Top Models by Requests"
                icon={Layers}
                columns={[
                  { key: 'model', label: 'Model' },
                  { key: 'provider', label: 'Provider' },
                  { key: 'requests', label: 'Requests', render: (v) => formatNumber(v) },
                  { key: 'tokens', label: 'Tokens', render: (v) => formatNumber(v) },
                  { key: 'cost', label: 'Cost', render: (v) => formatINR(v) },
                  { key: 'avg_latency_ms', label: 'Avg Latency', render: (v) => `${v?.toFixed(0) || 0}ms` }
                ]}
                data={topModels}
                emptyMessage="No model usage data"
              />
            </div>
          )}

          {activeTab === 'apikeys' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-900">API Key Usage</h2>
              <DataTable
                title="Usage by API Key"
                icon={Key}
                columns={[
                  { key: 'key_name', label: 'API Key' },
                  { key: 'requests', label: 'Requests', render: (v) => formatNumber(v) },
                  { key: 'tokens', label: 'Tokens', render: (v) => formatNumber(v) },
                  { key: 'cost', label: 'Cost', render: (v) => formatINR(v) },
                  { key: 'avg_latency_ms', label: 'Avg Latency', render: (v) => `${v?.toFixed(0) || 0}ms` },
                  { key: 'success_rate', label: 'Success Rate', render: (v) => `${v}%` }
                ]}
                data={byApiKey}
                emptyMessage="No API key usage data"
              />
            </div>
          )}

          {activeTab === 'users' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-900">User Usage</h2>
              <DataTable
                title="Top Users by Usage"
                icon={Users}
                columns={[
                  { key: 'user_name', label: 'User' },
                  { key: 'user_email', label: 'Email' },
                  { key: 'requests', label: 'Requests', render: (v) => formatNumber(v) },
                  { key: 'tokens', label: 'Tokens', render: (v) => formatNumber(v) },
                  { key: 'cost', label: 'Cost', render: (v) => formatINR(v) }
                ]}
                data={byUser}
                emptyMessage="No user usage data"
              />
            </div>
          )}

          {activeTab === 'departments' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-900">Department Usage</h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DataTable
                  title="Usage by Department"
                  icon={Building2}
                  columns={[
                    { key: 'department_name', label: 'Department' },
                    { key: 'requests', label: 'Requests', render: (v) => formatNumber(v) },
                    { key: 'tokens', label: 'Tokens', render: (v) => formatNumber(v) },
                    { key: 'cost', label: 'Cost', render: (v) => formatINR(v) }
                  ]}
                  data={byDepartment}
                  emptyMessage="No department data"
                />
                {byDepartment.length > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Cost Distribution</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={byDepartment}
                            dataKey="cost"
                            nameKey="department_name"
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            label={({ department_name, percent }) => `${department_name} (${(percent * 100).toFixed(0)}%)`}
                          >
                            {byDepartment.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => formatINR(value)} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-900">Performance Metrics</h2>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={Clock}
                  label="Avg Response Time"
                  value={`${(summary?.avg_latency_ms || 0).toFixed(0)}ms`}
                  color="bg-blue-500"
                />
                <StatCard
                  icon={CheckCircle}
                  label="Success Rate"
                  value={`${(summary?.success_rate || 100).toFixed(1)}%`}
                  color="bg-green-500"
                />
                <StatCard
                  icon={Zap}
                  label="Cache Hit Rate"
                  value={`${cacheStats?.hit_rate || 0}%`}
                  subvalue="Semantic cache"
                  color="bg-purple-500"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Requests/Day"
                  value={formatNumber(Math.round((summary?.total_requests || 0) / days))}
                  subvalue={`${days}-day average`}
                  color="bg-amber-500"
                />
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-900 mb-4">System Health</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <CheckCircle className="mx-auto text-green-500 mb-2" size={32} />
                    <p className="font-medium text-gray-900">API Gateway</p>
                    <p className="text-sm text-green-600">Healthy</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Database className="mx-auto text-green-500 mb-2" size={32} />
                    <p className="font-medium text-gray-900">Cache Service</p>
                    <p className="text-sm text-green-600">{cacheStats?.enabled ? 'Active' : 'Disabled'}</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Cpu className="mx-auto text-green-500 mb-2" size={32} />
                    <p className="font-medium text-gray-900">Load Balancer</p>
                    <p className="text-sm text-green-600">Healthy</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
