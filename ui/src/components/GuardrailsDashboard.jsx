import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, TrendingUp, Users, Building2, Key } from 'lucide-react';
import api from '../api/client';

export default function GuardrailsDashboard({ token }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    fetchStats();
  }, [timeRange]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/admin/guardrails/stats?range=${timeRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch guardrail stats:', err);
      // Show empty state instead of fake data
      setStats({
        total_requests: 0,
        blocked_requests: 0,
        redacted_requests: 0,
        passed_requests: 0,
        block_rate: 0,
        top_triggered_profiles: [],
        top_triggered_processors: [],
        by_department: [],
        trend: []
      });
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lime-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Guardrails Analytics</h3>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-lime-500"
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Shield size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(stats?.total_requests)}</p>
              <p className="text-sm text-gray-500">Total Requests</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle size={20} className="text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(stats?.blocked_requests)}</p>
              <p className="text-sm text-gray-500">Blocked</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Shield size={20} className="text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(stats?.redacted_requests)}</p>
              <p className="text-sm text-gray-500">Redacted</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.block_rate?.toFixed(2)}%</p>
              <p className="text-sm text-gray-500">Block Rate</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h4 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-lime-600" />
            Most Triggered Profiles
          </h4>
          <div className="space-y-3">
            {stats?.top_triggered_profiles?.map((profile, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                    idx === 0 ? 'bg-lime-100 text-lime-700' :
                    idx === 1 ? 'bg-blue-100 text-blue-700' :
                    idx === 2 ? 'bg-purple-100 text-purple-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {idx + 1}
                  </div>
                  <span className="text-sm font-medium text-gray-700">{profile.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">{profile.triggers} triggers</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    profile.block_rate > 2 ? 'bg-red-100 text-red-700' :
                    profile.block_rate > 1 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {profile.block_rate}% block
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h4 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={16} className="text-lime-600" />
            Processor Activity
          </h4>
          <div className="space-y-3">
            {stats?.top_triggered_processors?.map((proc, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    proc.type === 'pii_detection' ? 'bg-purple-500' :
                    proc.type === 'prompt_injection' ? 'bg-red-500' :
                    proc.type === 'toxicity_filter' ? 'bg-orange-500' :
                    'bg-blue-500'
                  }`} />
                  <span className="text-sm font-medium text-gray-700">
                    {proc.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">
                    {proc.action_breakdown?.block || 0} blocked
                  </span>
                  {proc.action_breakdown?.redact > 0 && (
                    <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                      {proc.action_breakdown.redact} redacted
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h4 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Building2 size={16} className="text-lime-600" />
          Department Breakdown
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="pb-3">Department</th>
                <th className="pb-3 text-right">Requests</th>
                <th className="pb-3 text-right">Blocked</th>
                <th className="pb-3 text-right">Block Rate</th>
                <th className="pb-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {stats?.by_department?.map((dept, idx) => {
                const blockRate = ((dept.blocked / dept.requests) * 100).toFixed(2);
                return (
                  <tr key={idx} className="text-sm">
                    <td className="py-3 font-medium text-gray-900">{dept.name}</td>
                    <td className="py-3 text-right text-gray-600">{formatNumber(dept.requests)}</td>
                    <td className="py-3 text-right text-gray-600">{dept.blocked}</td>
                    <td className="py-3 text-right text-gray-600">{blockRate}%</td>
                    <td className="py-3 text-right">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        parseFloat(blockRate) > 3 ? 'bg-red-100 text-red-700' :
                        parseFloat(blockRate) > 1.5 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {parseFloat(blockRate) > 3 ? 'High' : parseFloat(blockRate) > 1.5 ? 'Medium' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-gradient-to-r from-lime-50 to-green-50 border border-lime-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Shield size={20} className="text-lime-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-gray-900">Hierarchical Resolution Active</h4>
            <p className="text-xs text-gray-600 mt-1">
              Guardrail profiles are resolved in order: Route Policy → API Key → Team → Department → Tenant → System Default.
              This ensures the most specific configuration is always applied.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
