import { useState, useEffect } from 'react';
import { X, ArrowRight, Plus, Trash2 } from 'lucide-react';
import api from '../api/client';

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];

export default function RouteSetupModal({ isOpen, onClose, onSave, editRoute, token }) {
  const [formData, setFormData] = useState({
    path: '',
    name: '',
    description: '',
    allowed_methods: ['POST'],
    is_active: true,
    rate_limit_rpm: 0,
    rate_limit_tpm: 0,
    default_provider_id: null,
    default_model: '',
    policy_id: null,
    profile_id: null,
    allowed_models: '',
    strip_path_prefix: '',
    add_path_prefix: '',
    timeout_override: null,
    priority: 0
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [providers, setProviders] = useState([]);
  const [guardrailProfiles, setGuardrailProfiles] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetchProviders();
      fetchGuardrailProfiles();
      if (editRoute) {
        setFormData({
          path: editRoute.path || '',
          name: editRoute.name || '',
          description: editRoute.description || '',
          allowed_methods: editRoute.allowed_methods || ['POST'],
          is_active: editRoute.is_active !== false,
          rate_limit_rpm: editRoute.rate_limit_rpm || 0,
          rate_limit_tpm: editRoute.rate_limit_tpm || 0,
          default_provider_id: editRoute.default_provider_id || null,
          default_model: editRoute.default_model || '',
          policy_id: editRoute.policy_id || null,
          profile_id: editRoute.profile_id || null,
          allowed_models: editRoute.allowed_models?.join(', ') || '',
          strip_path_prefix: editRoute.strip_path_prefix || '',
          add_path_prefix: editRoute.add_path_prefix || '',
          timeout_override: editRoute.timeout_override || null,
          priority: editRoute.priority || 0
        });
      } else {
        setFormData({
          path: '',
          name: '',
          description: '',
          allowed_methods: ['POST'],
          is_active: true,
          rate_limit_rpm: 0,
          rate_limit_tpm: 0,
          default_provider_id: null,
          default_model: '',
          policy_id: null,
          profile_id: null,
          allowed_models: '',
          strip_path_prefix: '',
          add_path_prefix: '',
          timeout_override: null,
          priority: 0
        });
      }
      setError(null);
    }
  }, [isOpen, editRoute]);

  const fetchProviders = async () => {
    try {
      const response = await api.get('/admin/providers', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProviders(response.data || []);
    } catch (err) {
      console.error('Failed to fetch providers:', err);
    }
  };

  const fetchGuardrailProfiles = async () => {
    try {
      const response = await api.get('/admin/providers/profiles/list', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGuardrailProfiles(response.data || []);
    } catch (err) {
      console.error('Failed to fetch guardrail profiles:', err);
      setGuardrailProfiles([]);
    }
  };

  const handleSubmit = async () => {
    if (!formData.path) {
      setError('Path is required');
      return;
    }

    if (!formData.path.startsWith('/')) {
      setError('Path must start with /');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const allowedModelsArray = formData.allowed_models
        ? formData.allowed_models.split(',').map(m => m.trim()).filter(m => m)
        : null;
      
      const payload = {
        ...formData,
        rate_limit_rpm: formData.rate_limit_rpm || null,
        rate_limit_tpm: formData.rate_limit_tpm || null,
        timeout_override: formData.timeout_override || null,
        allowed_models: allowedModelsArray
      };

      if (editRoute?.id) {
        await api.put(`/admin/providers/routes/${editRoute.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/admin/providers/routes', payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      onSave();
      onClose();
    } catch (err) {
      console.error('Failed to save route:', err);
      setError(err.response?.data?.detail || 'Failed to save route');
    } finally {
      setSaving(false);
    }
  };

  const toggleMethod = (method) => {
    if (formData.allowed_methods.includes(method)) {
      if (formData.allowed_methods.length > 1) {
        setFormData({ ...formData, allowed_methods: formData.allowed_methods.filter(m => m !== method) });
      }
    } else {
      setFormData({ ...formData, allowed_methods: [...formData.allowed_methods, method] });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <ArrowRight size={24} className="text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900">
              {editRoute ? 'Edit API Route' : 'Create API Route'}
            </h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Path <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.path}
                onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                placeholder="/custom/endpoint"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
              />
              <p className="text-xs text-gray-500 mt-1">Route path pattern (e.g., /api/custom)</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Custom Endpoint"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what this route does..."
              rows={2}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">HTTP Methods</label>
            <div className="flex flex-wrap gap-2">
              {HTTP_METHODS.map((method) => (
                <button
                  key={method}
                  onClick={() => toggleMethod(method)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm ${
                    formData.allowed_methods.includes(method)
                      ? method === 'GET' ? 'bg-green-600 text-white' :
                        method === 'POST' ? 'bg-blue-600 text-white' :
                        method === 'PUT' ? 'bg-yellow-600 text-white' :
                        method === 'DELETE' ? 'bg-red-600 text-white' :
                        'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {method}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (req/min)</label>
              <input
                type="number"
                value={formData.rate_limit_rpm || ''}
                onChange={(e) => setFormData({ ...formData, rate_limit_rpm: parseInt(e.target.value) || 0 })}
                placeholder="0 = unlimited"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Token Limit (tokens/min)</label>
              <input
                type="number"
                value={formData.rate_limit_tpm || ''}
                onChange={(e) => setFormData({ ...formData, rate_limit_tpm: parseInt(e.target.value) || 0 })}
                placeholder="0 = unlimited"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Provider</label>
              <select
                value={formData.default_provider_id || ''}
                onChange={(e) => setFormData({ ...formData, default_provider_id: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500 focus:border-lime-500"
              >
                <option value="">Use Global Default</option>
                {providers.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.display_name || provider.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Model</label>
              <input
                type="text"
                value={formData.default_model}
                onChange={(e) => setFormData({ ...formData, default_model: e.target.value })}
                placeholder="e.g., gpt-4o"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lime-500 focus:border-lime-500"
              />
            </div>
          </div>

          <div className="bg-lime-50 border border-lime-200 rounded-xl p-4 space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-800 mb-2">Guardrail Profile</label>
              <select
                value={formData.profile_id || ''}
                onChange={(e) => setFormData({ ...formData, profile_id: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-4 py-2 border border-lime-300 rounded-lg focus:ring-2 focus:ring-lime-500 focus:border-lime-500 bg-white"
              >
                <option value="">Use Default (Tenant/API Key Level)</option>
                {guardrailProfiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} {profile.description ? `- ${profile.description.substring(0, 40)}...` : ''}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-600 mt-1">
                Override the guardrail profile for this specific route. Leave empty to use hierarchical resolution.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-800 mb-2">Allowed Models</label>
              <input
                type="text"
                value={formData.allowed_models}
                onChange={(e) => setFormData({ ...formData, allowed_models: e.target.value })}
                placeholder="gpt-4o, gpt-4o-mini, claude-3-sonnet"
                className="w-full px-4 py-2 border border-lime-300 rounded-lg focus:ring-2 focus:ring-lime-500 focus:border-lime-500 bg-white font-mono text-sm"
              />
              <p className="text-xs text-gray-600 mt-1">
                Comma-separated list of allowed models. Leave empty to allow all models.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Timeout Override (seconds)</label>
              <input
                type="number"
                value={formData.timeout_override || ''}
                onChange={(e) => setFormData({ ...formData, timeout_override: parseInt(e.target.value) || null })}
                placeholder="Default: use provider timeout"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <input
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                placeholder="0"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Higher priority routes match first</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Strip Path Prefix</label>
              <input
                type="text"
                value={formData.strip_path_prefix}
                onChange={(e) => setFormData({ ...formData, strip_path_prefix: e.target.value })}
                placeholder="/api/v1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Add Path Prefix</label>
              <input
                type="text"
                value={formData.add_path_prefix}
                onChange={(e) => setFormData({ ...formData, add_path_prefix: e.target.value })}
                placeholder="/v2"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Route Active</span>
            </label>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !formData.path}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : editRoute ? 'Update Route' : 'Create Route'}
          </button>
        </div>
      </div>
    </div>
  );
}
