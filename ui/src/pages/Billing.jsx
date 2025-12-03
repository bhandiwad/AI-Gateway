import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { 
  DollarSign, 
  Download, 
  TrendingUp, 
  Users, 
  FileText,
  Calendar,
  RefreshCw,
  AlertTriangle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function Billing() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [userBilling, setUserBilling] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('current_month');
  const [expandedUser, setExpandedUser] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchBillingData();
  }, [token, period]);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryRes, forecastRes] = await Promise.all([
        api.get(`/admin/billing/summary?period=${period}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/billing/forecast', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setSummary(summaryRes.data);
      setForecast(forecastRes.data);

      if (summaryRes.data.user_breakdown) {
        setUserBilling(summaryRes.data.user_breakdown);
      }
    } catch (err) {
      console.error('Failed to fetch billing data:', err);
      setError('Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const generateInvoice = async () => {
    try {
      setGenerating(true);
      const response = await api.post('/admin/billing/invoice', {
        period
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to generate invoice:', err);
      setError('Failed to generate invoice');
    } finally {
      setGenerating(false);
    }
  };

  const exportCSV = async () => {
    try {
      const response = await api.get(`/admin/billing/export/csv?period=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `usage-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      setError('Failed to export usage data');
    }
  };

  const USD_TO_INR = 83.5;
  
  const formatCurrency = (amount) => {
    const inrAmount = (amount || 0) * USD_TO_INR;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(inrAmount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-IN').format(num || 0);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Billing & Usage</h1>
            <p className="text-gray-600 mt-1">Monitor costs and generate invoices</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[44px]"
            >
              <option value="current_month">Current Month</option>
              <option value="last_month">Last Month</option>
              <option value="last_7_days">Last 7 Days</option>
              <option value="last_30_days">Last 30 Days</option>
            </select>
            <button
              onClick={fetchBillingData}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
            >
              <RefreshCw size={18} />
            </button>
            <button
              onClick={exportCSV}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
            >
              <Download size={18} />
              <span className="hidden sm:inline">Export CSV</span>
            </button>
            <button
              onClick={generateInvoice}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
            >
              <FileText size={18} />
              <span>{generating ? 'Generating...' : 'Generate Invoice'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="text-green-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Cost</p>
                <p className="text-xl font-bold">{formatCurrency(summary?.total_cost)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrendingUp className="text-blue-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Tokens</p>
                <p className="text-xl font-bold">{formatNumber(summary?.total_tokens)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="text-purple-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Users</p>
                <p className="text-xl font-bold">{summary?.active_users || 0}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Calendar className="text-orange-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Requests</p>
                <p className="text-xl font-bold">{formatNumber(summary?.total_requests)}</p>
              </div>
            </div>
          </div>
        </div>

        {forecast && (
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow p-6 mb-6 text-white">
            <h3 className="text-lg font-semibold mb-4">Cost Forecast</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-blue-100 text-sm">Daily Average</p>
                <p className="text-2xl font-bold">{formatCurrency(forecast.daily_average)}</p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Projected Monthly</p>
                <p className="text-2xl font-bold">{formatCurrency(forecast.projected_monthly)}</p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Trend</p>
                <p className="text-2xl font-bold flex items-center gap-2">
                  {forecast.trend > 0 ? (
                    <>
                      <TrendingUp size={24} />
                      +{forecast.trend?.toFixed(1)}%
                    </>
                  ) : (
                    <>
                      <TrendingUp size={24} className="rotate-180" />
                      {forecast.trend?.toFixed(1)}%
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold mb-4">Cost by Model</h3>
            {summary?.model_breakdown && summary.model_breakdown.length > 0 ? (
              <div className="space-y-3">
                {summary.model_breakdown.map((model, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500" style={{ 
                        backgroundColor: `hsl(${idx * 60}, 70%, 50%)` 
                      }}></div>
                      <span className="text-sm font-medium">{model.model}</span>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatCurrency(model.cost)}</p>
                      <p className="text-xs text-gray-500">{formatNumber(model.tokens)} tokens</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No usage data available</p>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold mb-4">Cost by Provider</h3>
            {summary?.provider_breakdown && summary.provider_breakdown.length > 0 ? (
              <div className="space-y-3">
                {summary.provider_breakdown.map((provider, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium capitalize">{provider.provider}</span>
                      <span className="font-medium">{formatCurrency(provider.cost)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full" 
                        style={{ 
                          width: `${(provider.cost / (summary.total_cost || 1)) * 100}%`,
                          backgroundColor: `hsl(${idx * 60}, 70%, 50%)`
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No usage data available</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-semibold">User Breakdown</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requests</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tokens</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(!userBilling || userBilling.length === 0) ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                      No user billing data available
                    </td>
                  </tr>
                ) : (
                  userBilling.map((user) => (
                    <>
                      <tr key={user.user_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-gray-900">{user.user_name || `User ${user.user_id}`}</p>
                            <p className="text-sm text-gray-500">{user.email}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3">{formatNumber(user.requests)}</td>
                        <td className="px-4 py-3">{formatNumber(user.tokens)}</td>
                        <td className="px-4 py-3 font-medium">{formatCurrency(user.cost)}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setExpandedUser(expandedUser === user.user_id ? null : user.user_id)}
                            className="text-blue-600 hover:text-blue-800 p-2"
                          >
                            {expandedUser === user.user_id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                          </button>
                        </td>
                      </tr>
                      {expandedUser === user.user_id && user.model_usage && (
                        <tr>
                          <td colSpan="5" className="px-4 py-3 bg-gray-50">
                            <div className="pl-4">
                              <p className="text-sm font-medium text-gray-700 mb-2">Model Usage</p>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                {user.model_usage.map((model, idx) => (
                                  <div key={idx} className="bg-white p-2 rounded border text-sm">
                                    <p className="font-medium">{model.model}</p>
                                    <p className="text-gray-500">{formatNumber(model.tokens)} tokens</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
