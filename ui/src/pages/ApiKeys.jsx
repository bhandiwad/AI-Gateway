import { useState, useEffect } from 'react';
import { apiKeysApi } from '../api/client';
import Header from '../components/Header';
import api from '../api/client';
import { Key, Plus, Trash2, Copy, Check, AlertTriangle, Settings, ChevronDown, ChevronUp } from 'lucide-react';

export default function ApiKeys() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createdKey, setCreatedKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const [creating, setCreating] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [providers, setProviders] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [users, setUsers] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    environment: 'production',
    department_id: null,
    team_id: null,
    owner_user_id: null,
    tags: '',
    guardrail_profile_id: null,
    default_provider_id: null,
    rate_limit_override: null,
    cost_limit_daily: null,
    cost_limit_monthly: null
  });

  useEffect(() => {
    loadApiKeys();
    loadProfiles();
    loadProviders();
    loadDepartments();
    loadTeams();
    loadUsers();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await apiKeysApi.list();
      setApiKeys(response.data);
    } catch (error) {
      console.error('Failed to load API keys:', error);
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

  const loadDepartments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/admin/organization/departments', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDepartments(response.data || []);
    } catch (error) {
      console.error('Failed to load departments:', error);
    }
  };

  const loadTeams = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/admin/organization/teams', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeams(response.data || []);
    } catch (error) {
      console.error('Failed to load teams:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/admin/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setCreating(true);
    try {
      const payload = {
        name: formData.name,
        environment: formData.environment,
        department_id: formData.department_id || undefined,
        team_id: formData.team_id || undefined,
        owner_user_id: formData.owner_user_id || undefined,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(t => t) : undefined,
        guardrail_profile_id: formData.guardrail_profile_id || undefined,
        default_provider_id: formData.default_provider_id || undefined,
        rate_limit_override: formData.rate_limit_override || undefined,
        cost_limit_daily: formData.cost_limit_daily || undefined,
        cost_limit_monthly: formData.cost_limit_monthly || undefined
      };
      const response = await apiKeysApi.create(payload);
      setCreatedKey(response.data.api_key);
      setApiKeys([response.data, ...apiKeys]);
      setFormData({
        name: '',
        environment: 'production',
        department_id: null,
        team_id: null,
        owner_user_id: null,
        tags: '',
        guardrail_profile_id: null,
        default_provider_id: null,
        rate_limit_override: null,
        cost_limit_daily: null,
        cost_limit_monthly: null
      });
    } catch (error) {
      console.error('Failed to create API key:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (id) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;

    try {
      await apiKeysApi.revoke(id);
      setApiKeys(apiKeys.map(k => k.id === id ? { ...k, is_active: false } : k));
    } catch (error) {
      console.error('Failed to revoke API key:', error);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(createdKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getEnvironmentBadge = (env) => {
    const styles = {
      production: 'bg-red-100 text-red-800',
      staging: 'bg-yellow-100 text-yellow-800',
      development: 'bg-blue-100 text-blue-800'
    };
    return styles[env] || styles.production;
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="API Keys" />
      
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <p className="text-gray-500">
              Manage your API keys for accessing the AI Gateway
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
            >
              <Plus size={18} />
              Create New Key
            </button>
          </div>

          {showCreate && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Create New API Key</h3>
              
              {createdKey ? (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800 mb-2">
                      Your API key has been created. Copy it now - you won't be able to see it again!
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 p-2 bg-white border border-green-300 rounded text-sm font-mono break-all">
                        {createdKey}
                      </code>
                      <button
                        onClick={copyToClipboard}
                        className="p-2 text-green-600 hover:bg-green-100 rounded"
                      >
                        {copied ? <Check size={20} /> : <Copy size={20} />}
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setCreatedKey(null);
                      setShowCreate(false);
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <form onSubmit={handleCreate} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                        placeholder="e.g., Production Key"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
                      <select
                        value={formData.environment}
                        onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="production">Production</option>
                        <option value="staging">Staging</option>
                        <option value="development">Development</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                      <select
                        value={formData.department_id || ''}
                        onChange={(e) => setFormData({ ...formData, department_id: e.target.value ? parseInt(e.target.value) : null })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="">Select department</option>
                        {departments.map(d => (
                          <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Team</label>
                      <select
                        value={formData.team_id || ''}
                        onChange={(e) => setFormData({ ...formData, team_id: e.target.value ? parseInt(e.target.value) : null })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="">Select team</option>
                        {teams.filter(t => !formData.department_id || t.department_id === formData.department_id).map(t => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
                      <select
                        value={formData.owner_user_id || ''}
                        onChange={(e) => setFormData({ ...formData, owner_user_id: e.target.value ? parseInt(e.target.value) : null })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                      >
                        <option value="">Select owner</option>
                        {users.map(u => (
                          <option key={u.id} value={u.id}>{u.name} ({u.email})</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                    <input
                      type="text"
                      value={formData.tags}
                      onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                      placeholder="e.g., production, backend, api"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                    />
                    <p className="mt-1 text-xs text-gray-500">Comma-separated tags for organization</p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
                  >
                    <Settings size={16} />
                    Advanced Options
                    {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {showAdvanced && (
                    <div className="space-y-4 pt-4 border-t border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Guardrail Profile</label>
                          <select
                            value={formData.guardrail_profile_id || ''}
                            onChange={(e) => setFormData({ ...formData, guardrail_profile_id: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                          >
                            <option value="">Use Default</option>
                            {profiles.map(p => (
                              <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                          </select>
                          <p className="mt-1 text-xs text-gray-500">Override default guardrail profile for this key</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Default Provider</label>
                          <select
                            value={formData.default_provider_id || ''}
                            onChange={(e) => setFormData({ ...formData, default_provider_id: e.target.value ? parseInt(e.target.value) : null })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                          >
                            <option value="">Use Default</option>
                            {providers.map(p => (
                              <option key={p.id} value={p.id}>{p.name || p.display_name}</option>
                            ))}
                          </select>
                          <p className="mt-1 text-xs text-gray-500">Override default provider for this key</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit Override</label>
                          <input
                            type="number"
                            value={formData.rate_limit_override || ''}
                            onChange={(e) => setFormData({ ...formData, rate_limit_override: e.target.value ? parseInt(e.target.value) : null })}
                            placeholder="requests/min"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Daily Cost Limit</label>
                          <div className="relative">
                            <span className="absolute left-3 top-2 text-gray-500">₹</span>
                            <input
                              type="number"
                              value={formData.cost_limit_daily || ''}
                              onChange={(e) => setFormData({ ...formData, cost_limit_daily: e.target.value ? parseFloat(e.target.value) : null })}
                              placeholder="0.00"
                              className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            />
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Cost Limit</label>
                          <div className="relative">
                            <span className="absolute left-3 top-2 text-gray-500">₹</span>
                            <input
                              type="number"
                              value={formData.cost_limit_monthly || ''}
                              onChange={(e) => setFormData({ ...formData, cost_limit_monthly: e.target.value ? parseFloat(e.target.value) : null })}
                              placeholder="0.00"
                              className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end gap-3 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreate(false);
                        setShowAdvanced(false);
                      }}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={creating || !formData.name.trim()}
                      className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
                    >
                      {creating ? 'Creating...' : 'Create API Key'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Key Prefix
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Environment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Used
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {apiKeys.map((key) => (
                    <tr key={key.id} className={!key.is_active ? 'bg-gray-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Key size={16} className="text-gray-400" />
                          <span className="font-medium text-gray-800">{key.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <code className="text-sm text-gray-500">{key.key_prefix}...</code>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getEnvironmentBadge(key.environment)}`}>
                          {key.environment || 'production'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {key.is_active ? (
                          <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                            Revoked
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {key.last_used_at 
                          ? new Date(key.last_used_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(key.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {key.is_active && (
                          <button
                            onClick={() => handleRevoke(key.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {apiKeys.length === 0 && (
                <div className="text-center py-12">
                  <Key className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500">No API keys yet</p>
                  <button
                    onClick={() => setShowCreate(true)}
                    className="mt-4 text-gray-700 hover:underline"
                  >
                    Create your first API key
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-3">
              <AlertTriangle className="text-amber-500 flex-shrink-0" size={20} />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Keep your API keys secure</p>
                <p className="mt-1">
                  Do not share your API keys in public repositories or client-side code. 
                  Revoke any keys that may have been compromised.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
