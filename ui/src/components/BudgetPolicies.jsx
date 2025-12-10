import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { 
  DollarSign, 
  Plus, 
  Trash2, 
  Edit2, 
  Save, 
  X,
  ToggleLeft,
  ToggleRight,
  AlertTriangle,
  Check,
  Filter,
  Users,
  Building,
  Key,
  Route as RouteIcon,
  Cpu
} from 'lucide-react';

const SCOPE_ICONS = {
  tenant: Building,
  department: Building,
  team: Users,
  api_key: Key,
  user: Users,
  route: RouteIcon,
  model: Cpu,
  global: DollarSign
};

const SCOPE_LABELS = {
  tenant: 'Organization',
  department: 'Department',
  team: 'Team',
  api_key: 'API Key',
  user: 'User',
  route: 'API Route',
  model: 'Model',
  global: 'Global'
};

export default function BudgetPolicies() {
  const { token } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [scopeOptions, setScopeOptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [saving, setSaving] = useState(false);

  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    scope_type: 'tenant',
    scope_id: null,
    model_filter: '',
    period: 'monthly',
    hard_limit_usd: '',
    action_on_limit: 'block',
    enabled: false,
    soft_threshold_pct: 80,
    warning_threshold_pct: 90,
    critical_threshold_pct: 95
  });

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [policiesRes, scopeRes] = await Promise.all([
        api.get('/admin/budget/policies', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/budget/scope-options', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setPolicies(policiesRes.data.policies || []);
      setScopeOptions(scopeRes.data);
    } catch (err) {
      console.error('Failed to fetch budget policies:', err);
      setError('Failed to load budget policies');
    } finally {
      setLoading(false);
    }
  };

  const createPolicy = async () => {
    if (!newPolicy.name || !newPolicy.hard_limit_usd) {
      setError('Name and limit are required');
      return;
    }

    try {
      setSaving(true);
      await api.post('/admin/budget/policies', {
        ...newPolicy,
        hard_limit_usd: parseFloat(newPolicy.hard_limit_usd),
        scope_id: newPolicy.scope_id || null,
        model_filter: newPolicy.model_filter || null
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowCreateModal(false);
      setNewPolicy({
        name: '',
        description: '',
        scope_type: 'tenant',
        scope_id: null,
        model_filter: '',
        period: 'monthly',
        hard_limit_usd: '',
        action_on_limit: 'block',
        enabled: false,
        soft_threshold_pct: 80,
        warning_threshold_pct: 90,
        critical_threshold_pct: 95
      });
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create policy');
    } finally {
      setSaving(false);
    }
  };

  const togglePolicy = async (policyId) => {
    try {
      await api.post(`/admin/budget/policies/${policyId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      setError('Failed to toggle policy');
    }
  };

  const deletePolicy = async (policyId) => {
    if (!confirm('Are you sure you want to delete this budget policy?')) return;
    
    try {
      await api.delete(`/admin/budget/policies/${policyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      setError('Failed to delete policy');
    }
  };

  const getWarningColor = (level) => {
    switch (level) {
      case 'exceeded': return 'bg-red-500';
      case 'critical': return 'bg-red-400';
      case 'warning': return 'bg-amber-500';
      case 'soft': return 'bg-yellow-400';
      default: return 'bg-lime-500';
    }
  };

  const USD_TO_INR = 83.5;
  const formatCurrency = (amount) => {
    const inrAmount = (amount || 0) * USD_TO_INR;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(inrAmount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lime-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Budget Policies</h3>
          <p className="text-sm text-gray-500">Granular spending controls by scope (disabled by default)</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-lime-600 text-white rounded-lg hover:bg-lime-700"
        >
          <Plus size={18} />
          Add Policy
        </button>
      </div>

      {error && (
        <div className="mx-4 mt-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2">
          <AlertTriangle size={18} className="text-red-500" />
          <span className="text-red-700 text-sm">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="p-4">
        {policies.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <DollarSign size={48} className="mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No budget policies configured</p>
            <p className="text-sm mt-1">Create policies to control spending at different levels</p>
            <p className="text-xs mt-2 text-gray-400">Budgets are disabled by default until you enable them</p>
          </div>
        ) : (
          <div className="space-y-3">
            {policies.map(policy => {
              const ScopeIcon = SCOPE_ICONS[policy.scope_type] || DollarSign;
              return (
                <div 
                  key={policy.id} 
                  className={`border rounded-lg p-4 ${policy.enabled ? 'border-lime-200 bg-lime-50/30' : 'border-gray-200 bg-gray-50'}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${policy.enabled ? 'bg-lime-100' : 'bg-gray-100'}`}>
                        <ScopeIcon size={20} className={policy.enabled ? 'text-lime-600' : 'text-gray-400'} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{policy.name}</h4>
                          {!policy.enabled && (
                            <span className="text-xs px-2 py-0.5 bg-gray-200 text-gray-600 rounded-full">Disabled</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 mt-0.5">
                          {SCOPE_LABELS[policy.scope_type]}
                          {policy.model_filter && ` • Model: ${policy.model_filter}`}
                          {` • ${policy.period.charAt(0).toUpperCase() + policy.period.slice(1)}`}
                        </p>
                        {policy.description && (
                          <p className="text-xs text-gray-400 mt-1">{policy.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => togglePolicy(policy.id)}
                        className={`p-2 rounded-lg transition-colors ${
                          policy.enabled 
                            ? 'text-lime-600 hover:bg-lime-100' 
                            : 'text-gray-400 hover:bg-gray-100'
                        }`}
                        title={policy.enabled ? 'Disable policy' : 'Enable policy'}
                      >
                        {policy.enabled ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
                      </button>
                      <button
                        onClick={() => deletePolicy(policy.id)}
                        className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-500">Limit</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(policy.hard_limit_usd)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Current Usage</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(policy.current_usage_usd)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Used</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${getWarningColor(policy.warning_level)}`}
                            style={{ width: `${Math.min(policy.percentage_used, 100)}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{policy.percentage_used}%</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Action</p>
                      <p className={`text-sm font-medium ${policy.action_on_limit === 'block' ? 'text-red-600' : 'text-amber-600'}`}>
                        {policy.action_on_limit === 'block' ? 'Block' : 'Warn'}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900">Create Budget Policy</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700">
                <strong>Note:</strong> Budget policies are disabled by default. You can enable them after creation.
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Policy Name *</label>
                <input
                  type="text"
                  value={newPolicy.name}
                  onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                  placeholder="e.g., GPT-4 Monthly Limit"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newPolicy.description}
                  onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                  placeholder="Optional description"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Scope *</label>
                  <select
                    value={newPolicy.scope_type}
                    onChange={(e) => setNewPolicy({ ...newPolicy, scope_type: e.target.value, scope_id: null })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                  >
                    {scopeOptions?.scopes?.map(scope => (
                      <option key={scope.type} value={scope.type}>{scope.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Period *</label>
                  <select
                    value={newPolicy.period}
                    onChange={(e) => setNewPolicy({ ...newPolicy, period: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                  >
                    {scopeOptions?.periods?.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {scopeOptions?.scopes?.find(s => s.type === newPolicy.scope_type)?.options?.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select {SCOPE_LABELS[newPolicy.scope_type]}
                  </label>
                  <select
                    value={newPolicy.scope_id || ''}
                    onChange={(e) => setNewPolicy({ ...newPolicy, scope_id: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                  >
                    <option value="">All {SCOPE_LABELS[newPolicy.scope_type]}s</option>
                    {scopeOptions.scopes.find(s => s.type === newPolicy.scope_type)?.options?.map(opt => (
                      <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model Filter (optional)</label>
                <input
                  type="text"
                  value={newPolicy.model_filter}
                  onChange={(e) => setNewPolicy({ ...newPolicy, model_filter: e.target.value })}
                  placeholder="e.g., gpt-4, claude-3-opus"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                />
                <p className="text-xs text-gray-500 mt-1">Leave empty to apply to all models</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spending Limit (USD) *</label>
                  <input
                    type="number"
                    value={newPolicy.hard_limit_usd}
                    onChange={(e) => setNewPolicy({ ...newPolicy, hard_limit_usd: e.target.value })}
                    placeholder="e.g., 100"
                    min="0"
                    step="0.01"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Action on Limit</label>
                  <select
                    value={newPolicy.action_on_limit}
                    onChange={(e) => setNewPolicy({ ...newPolicy, action_on_limit: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500"
                  >
                    {scopeOptions?.actions?.map(a => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Alert Thresholds</label>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-gray-500">Soft (%)</label>
                    <input
                      type="number"
                      value={newPolicy.soft_threshold_pct}
                      onChange={(e) => setNewPolicy({ ...newPolicy, soft_threshold_pct: parseInt(e.target.value) })}
                      min="0"
                      max="100"
                      className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-lime-500 text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">Warning (%)</label>
                    <input
                      type="number"
                      value={newPolicy.warning_threshold_pct}
                      onChange={(e) => setNewPolicy({ ...newPolicy, warning_threshold_pct: parseInt(e.target.value) })}
                      min="0"
                      max="100"
                      className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-lime-500 text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">Critical (%)</label>
                    <input
                      type="number"
                      value={newPolicy.critical_threshold_pct}
                      onChange={(e) => setNewPolicy({ ...newPolicy, critical_threshold_pct: parseInt(e.target.value) })}
                      min="0"
                      max="100"
                      className="w-full px-3 py-1.5 border border-gray-300 rounded focus:ring-2 focus:ring-lime-500 text-sm"
                    />
                  </div>
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer pt-2">
                <input
                  type="checkbox"
                  checked={newPolicy.enabled}
                  onChange={(e) => setNewPolicy({ ...newPolicy, enabled: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-lime-600 focus:ring-lime-500"
                />
                <span className="text-sm text-gray-700">Enable policy immediately</span>
              </label>
            </div>

            <div className="p-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={createPolicy}
                disabled={saving || !newPolicy.name || !newPolicy.hard_limit_usd}
                className="px-4 py-2 bg-lime-600 text-white rounded-lg hover:bg-lime-700 disabled:opacity-50"
              >
                {saving ? 'Creating...' : 'Create Policy'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
