import { useState, useEffect } from 'react';
import { tenantsApi } from '../api/client';
import api from '../api/client';
import Header from '../components/Header';
import { Users, Search, Edit2, CheckCircle, XCircle, Settings, ChevronDown, ChevronUp, Save, X } from 'lucide-react';

export default function Tenants() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [providers, setProviders] = useState([]);
  const [editData, setEditData] = useState({});

  useEffect(() => {
    loadTenants();
    loadProfiles();
    loadProviders();
  }, []);

  const loadTenants = async () => {
    try {
      const response = await tenantsApi.list();
      setTenants(response.data);
    } catch (error) {
      console.error('Failed to load tenants:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadProfiles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/admin/providers/profiles/list', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfiles(response.data || []);
    } catch (error) {
      console.error('Failed to load profiles:', error);
    }
  };

  const loadProviders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/admin/providers', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProviders(response.data || []);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const handleEdit = (tenant) => {
    setEditingId(tenant.id);
    setEditData({
      rate_limit: tenant.rate_limit,
      monthly_budget: tenant.monthly_budget,
      is_active: tenant.is_active,
      cost_ceiling_daily: tenant.cost_ceiling_daily || '',
      cost_ceiling_monthly: tenant.cost_ceiling_monthly || '',
      logging_policy: tenant.logging_policy || 'full',
      guardrail_profile_id: tenant.guardrail_profile_id || '',
      default_provider_id: tenant.default_provider_id || '',
      allowed_providers: tenant.allowed_providers || [],
      allowed_models: tenant.allowed_models || []
    });
    setShowAdvanced(false);
  };

  const handleSave = async (id) => {
    try {
      const payload = {
        ...editData,
        cost_ceiling_daily: editData.cost_ceiling_daily ? parseFloat(editData.cost_ceiling_daily) : null,
        cost_ceiling_monthly: editData.cost_ceiling_monthly ? parseFloat(editData.cost_ceiling_monthly) : null,
        guardrail_profile_id: editData.guardrail_profile_id ? parseInt(editData.guardrail_profile_id) : null,
        default_provider_id: editData.default_provider_id ? parseInt(editData.default_provider_id) : null,
        allowed_providers: editData.allowed_providers || [],
        allowed_models: editData.allowed_models || []
      };
      await tenantsApi.update(id, payload);
      setTenants(tenants.map(t => t.id === id ? { ...t, ...payload } : t));
      setEditingId(null);
      setShowAdvanced(false);
    } catch (error) {
      console.error('Failed to update tenant:', error);
    }
  };

  const toggleProvider = (providerId) => {
    const current = editData.allowed_providers || [];
    if (current.includes(providerId)) {
      setEditData({ ...editData, allowed_providers: current.filter(p => p !== providerId) });
    } else {
      setEditData({ ...editData, allowed_providers: [...current, providerId] });
    }
  };

  const toggleModel = (modelId) => {
    const current = editData.allowed_models || [];
    if (current.includes(modelId)) {
      setEditData({ ...editData, allowed_models: current.filter(m => m !== modelId) });
    } else {
      setEditData({ ...editData, allowed_models: [...current, modelId] });
    }
  };

  const filteredTenants = tenants.filter(tenant =>
    tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Tenant Management" />
      
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <p className="text-gray-500">
              Manage tenant accounts, limits, and compliance settings
            </p>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tenants..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
              />
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTenants.map((tenant) => (
                <div key={tenant.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                  <div className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                          <span className="text-gray-700 font-semibold text-lg">
                            {tenant.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-semibold text-gray-900">{tenant.name}</p>
                            {tenant.is_admin && (
                              <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-800 rounded-full">
                                Admin
                              </span>
                            )}
                            {tenant.is_active ? (
                              <span className="flex items-center gap-1 text-xs text-green-600">
                                <CheckCircle size={12} />
                                Active
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-xs text-red-600">
                                <XCircle size={12} />
                                Inactive
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">{tenant.email}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Rate Limit</p>
                          <p className="font-medium text-gray-900">{tenant.rate_limit}/min</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Budget</p>
                          <p className="font-medium text-gray-900">₹{((tenant.monthly_budget || 0) * 83.5).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Spend</p>
                          <p className="font-medium text-gray-900">₹{((tenant.current_spend || 0) * 83.5).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Created</p>
                          <p className="font-medium text-gray-900">{new Date(tenant.created_at).toLocaleDateString()}</p>
                        </div>
                        
                        {editingId !== tenant.id && (
                          <button
                            onClick={() => handleEdit(tenant)}
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                          >
                            <Edit2 size={18} />
                          </button>
                        )}
                      </div>
                    </div>

                    {editingId === tenant.id && (
                      <div className="mt-6 pt-6 border-t border-gray-200">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                            <select
                              value={editData.is_active ? 'active' : 'inactive'}
                              onChange={(e) => setEditData({
                                ...editData,
                                is_active: e.target.value === 'active'
                              })}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            >
                              <option value="active">Active</option>
                              <option value="inactive">Inactive</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (req/min)</label>
                            <input
                              type="number"
                              value={editData.rate_limit}
                              onChange={(e) => setEditData({
                                ...editData,
                                rate_limit: parseInt(e.target.value)
                              })}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Budget (USD)</label>
                            <input
                              type="number"
                              value={editData.monthly_budget}
                              onChange={(e) => setEditData({
                                ...editData,
                                monthly_budget: parseFloat(e.target.value)
                              })}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Logging Policy</label>
                            <select
                              value={editData.logging_policy}
                              onChange={(e) => setEditData({
                                ...editData,
                                logging_policy: e.target.value
                              })}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            >
                              <option value="full">Full Logging</option>
                              <option value="minimal">Minimal Logging</option>
                              <option value="none">No Logging</option>
                            </select>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => setShowAdvanced(!showAdvanced)}
                          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800 mb-4"
                        >
                          <Settings size={16} />
                          Cost Controls & Provider Settings
                          {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </button>

                        {showAdvanced && (
                          <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Daily Cost Ceiling (₹)</label>
                                <input
                                  type="number"
                                  value={editData.cost_ceiling_daily}
                                  onChange={(e) => setEditData({
                                    ...editData,
                                    cost_ceiling_daily: e.target.value
                                  })}
                                  placeholder="No limit"
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Maximum daily spend limit in INR</p>
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Cost Ceiling (₹)</label>
                                <input
                                  type="number"
                                  value={editData.cost_ceiling_monthly}
                                  onChange={(e) => setEditData({
                                    ...editData,
                                    cost_ceiling_monthly: e.target.value
                                  })}
                                  placeholder="No limit"
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                                />
                                <p className="mt-1 text-xs text-gray-500">Maximum monthly spend limit in INR</p>
                              </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Default Guardrail Profile</label>
                                <select
                                  value={editData.guardrail_profile_id}
                                  onChange={(e) => setEditData({
                                    ...editData,
                                    guardrail_profile_id: e.target.value
                                  })}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                                >
                                  <option value="">System Default</option>
                                  {profiles.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                  ))}
                                </select>
                                <p className="mt-1 text-xs text-gray-500">Guardrail profile applied to all tenant requests</p>
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Default Provider</label>
                                <select
                                  value={editData.default_provider_id}
                                  onChange={(e) => setEditData({
                                    ...editData,
                                    default_provider_id: e.target.value
                                  })}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                                >
                                  <option value="">System Default</option>
                                  {providers.map(p => (
                                    <option key={p.id} value={p.id}>{p.name || p.display_name}</option>
                                  ))}
                                </select>
                                <p className="mt-1 text-xs text-gray-500">Default AI provider for this tenant</p>
                              </div>
                            </div>

                            <div className="mt-4">
                              <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Providers</label>
                              <p className="text-xs text-gray-500 mb-2">Select which providers this tenant can use. Leave empty to allow all.</p>
                              <div className="flex flex-wrap gap-2">
                                {providers.length === 0 ? (
                                  <p className="text-sm text-gray-400 italic">No providers configured. Add providers in Router Config.</p>
                                ) : (
                                  providers.map(p => (
                                    <button
                                      key={p.id}
                                      type="button"
                                      onClick={() => toggleProvider(String(p.id))}
                                      className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                                        (editData.allowed_providers || []).includes(String(p.id))
                                          ? 'bg-gray-900 text-white border-gray-900'
                                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                      }`}
                                    >
                                      {p.name || p.display_name}
                                    </button>
                                  ))
                                )}
                              </div>
                            </div>

                            <div className="mt-4">
                              <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Models</label>
                              <p className="text-xs text-gray-500 mb-2">Enter model IDs this tenant can use (comma-separated). Leave empty to allow all.</p>
                              <input
                                type="text"
                                value={(editData.allowed_models || []).join(', ')}
                                onChange={(e) => {
                                  const models = e.target.value.split(',').map(m => m.trim()).filter(m => m);
                                  setEditData({ ...editData, allowed_models: models });
                                }}
                                placeholder="e.g., gpt-4, claude-3-opus, gemini-pro"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                              />
                            </div>
                          </div>
                        )}

                        <div className="flex justify-end gap-3 mt-4">
                          <button
                            onClick={() => {
                              setEditingId(null);
                              setShowAdvanced(false);
                            }}
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
                          >
                            <X size={16} />
                            Cancel
                          </button>
                          <button
                            onClick={() => handleSave(tenant.id)}
                            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 flex items-center gap-2"
                          >
                            <Save size={16} />
                            Save Changes
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {filteredTenants.length === 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                  <Users className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500">No tenants found</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
