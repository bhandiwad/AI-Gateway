import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import Header from '../components/Header';
import ProviderSetupModal from '../components/ProviderSetupModal';
import RouteSetupModal from '../components/RouteSetupModal';
import PolicyDesigner from '../components/PolicyDesigner';
import { 
  GitBranch, 
  Server, 
  Zap, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Save,
  Play,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Activity,
  Gauge,
  RotateCcw,
  Plus,
  Trash2,
  Copy,
  Check,
  Edit2,
  Globe,
  Clock,
  Settings
} from 'lucide-react';

export default function RouterConfig() {
  const { token, hasPermission } = useAuth();
  const [providers, setProviders] = useState([]);
  const [routingConfig, setRoutingConfig] = useState(null);
  const [fallbackChain, setFallbackChain] = useState(null);
  const [routingStats, setRoutingStats] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('providers');
  const [testModel, setTestModel] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [healthChecks, setHealthChecks] = useState([]);
  const [checkingHealth, setCheckingHealth] = useState(false);
  const [copied, setCopied] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [editingTierName, setEditingTierName] = useState(null);
  const [newTierName, setNewTierName] = useState('');
  const [providerModalOpen, setProviderModalOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [configuredProviders, setConfiguredProviders] = useState([]);
  const [apiRoutes, setApiRoutes] = useState([]);
  const [routeModalOpen, setRouteModalOpen] = useState(false);
  const [editingRoute, setEditingRoute] = useState(null);

  const canEdit = hasPermission('router:edit');

  const proxyUrl = typeof window !== 'undefined' 
    ? `${window.location.origin}/api/v1`
    : '';

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [providersRes, configRes, fallbackRes, modelsRes, statsRes, configuredProvidersRes, apiRoutesRes] = await Promise.all([
        api.get('/admin/router/providers', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/config', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/fallback-chain', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/models/settings', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/stats', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: { stats: [] } })),
        api.get('/admin/providers', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] })),
        api.get('/admin/providers/routes', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] }))
      ]);

      setProviders(providersRes.data.providers || []);
      setConfiguredProviders(configuredProvidersRes.data || []);
      setApiRoutes(apiRoutesRes.data || []);
      const config = configRes.data;
      if (!config.rate_limits_default) {
        const routing = config;
        config.rate_limits_default = {
          requests_per_minute: routing.rate_limits?.default?.requests_per_minute || 100,
          tokens_per_minute: routing.rate_limits?.default?.tokens_per_minute || 100000
        };
      }
      setRoutingConfig(config);
      setFallbackChain(fallbackRes.data);
      setModels(modelsRes.data.models || modelsRes.data.data || modelsRes.data || []);
      setRoutingStats(statsRes.data.stats || []);
      setHasChanges(false);

    } catch (err) {
      console.error('Failed to fetch router config:', err);
      setError('Failed to load router configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!canEdit) return;

    try {
      setSaving(true);
      setError(null);

      const updateData = {
        default_provider: routingConfig.default_provider,
        default_model: routingConfig.default_model,
        fallback_enabled: routingConfig.fallback?.enabled,
        max_retries: routingConfig.fallback?.max_retries,
        fallback_order: routingConfig.fallback?.fallback_order,
        rate_limit_tiers: routingConfig.rate_limit_tiers,
        default_rate_limit_requests: routingConfig.rate_limits_default?.requests_per_minute,
        default_rate_limit_tokens: routingConfig.rate_limits_default?.tokens_per_minute
      };

      await api.put('/admin/router/config', updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setSuccess('Configuration saved successfully');
      setHasChanges(false);
      setTimeout(() => setSuccess(null), 3000);
      
      await fetchData();
    } catch (err) {
      console.error('Failed to save config:', err);
      let errorMsg = 'Failed to save configuration';
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          errorMsg = err.response.data;
        } else if (err.response.data.detail) {
          if (typeof err.response.data.detail === 'string') {
            errorMsg = err.response.data.detail;
          } else if (Array.isArray(err.response.data.detail)) {
            errorMsg = err.response.data.detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
          } else {
            errorMsg = JSON.stringify(err.response.data.detail);
          }
        } else if (err.response.data.message) {
          errorMsg = err.response.data.message;
        }
      }
      setError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const checkHealth = async () => {
    try {
      setCheckingHealth(true);
      const response = await api.post('/admin/router/health-check', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHealthChecks(response.data.health_checks || []);
    } catch (err) {
      console.error('Health check failed:', err);
      setError('Failed to check provider health');
    } finally {
      setCheckingHealth(false);
    }
  };

  const testRoute = async () => {
    if (!testModel) return;

    try {
      setTesting(true);
      setTestResult(null);

      const response = await api.post('/chat/completions', {
        model: testModel,
        messages: [{ role: 'user', content: 'Test routing - respond with OK' }],
        max_tokens: 10
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setTestResult({
        success: true,
        model: response.data.model,
        latency: response.data.usage?.total_tokens ? 100 : 0,
        provider: models.find(m => m.id === testModel)?.provider || 'unknown'
      });
    } catch (err) {
      setTestResult({
        success: false,
        error: err.response?.data?.detail || err.message
      });
    } finally {
      setTesting(false);
    }
  };

  const updateConfig = (updates) => {
    setRoutingConfig(prev => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const updateFallback = (updates) => {
    setRoutingConfig(prev => ({
      ...prev,
      fallback: { ...prev.fallback, ...updates }
    }));
    setHasChanges(true);
  };

  const updateDefaultRateLimits = (field, value) => {
    setRoutingConfig(prev => ({
      ...prev,
      rate_limits_default: {
        ...prev.rate_limits_default,
        [field]: parseInt(value) || 0
      }
    }));
    setHasChanges(true);
  };

  const updateTier = (tierName, field, value) => {
    setRoutingConfig(prev => ({
      ...prev,
      rate_limit_tiers: prev.rate_limit_tiers.map(t =>
        t.name === tierName ? { ...t, [field]: field === 'name' ? value : (parseInt(value) || 0) } : t
      )
    }));
    setHasChanges(true);
  };

  const sanitizeTierName = (name) => {
    return name.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
  };

  const renameTier = (oldName, newName) => {
    const sanitized = sanitizeTierName(newName);
    if (!sanitized || sanitized === oldName) {
      setEditingTierName(null);
      setNewTierName('');
      return;
    }
    const exists = routingConfig.rate_limit_tiers.some(t => t.name === sanitized && t.name !== oldName);
    if (exists) {
      setError(`Tier name "${sanitized}" already exists`);
      setTimeout(() => setError(null), 3000);
      return;
    }
    updateTier(oldName, 'name', sanitized);
    setEditingTierName(null);
    setNewTierName('');
  };

  const addTier = () => {
    const existingNames = routingConfig.rate_limit_tiers.map(t => t.name);
    let newName = 'custom';
    let counter = 1;
    while (existingNames.includes(newName)) {
      newName = `custom_${counter}`;
      counter++;
    }
    setRoutingConfig(prev => ({
      ...prev,
      rate_limit_tiers: [
        ...prev.rate_limit_tiers,
        { name: newName, requests_per_minute: 100, tokens_per_minute: 100000 }
      ]
    }));
    setHasChanges(true);
  };

  const removeTier = (tierName) => {
    setRoutingConfig(prev => ({
      ...prev,
      rate_limit_tiers: prev.rate_limit_tiers.filter(t => t.name !== tierName)
    }));
    setHasChanges(true);
  };

  const addProviderToFallback = (provider) => {
    const currentOrder = routingConfig?.fallback?.fallback_order || [];
    if (!currentOrder.includes(provider)) {
      updateFallback({ fallback_order: [...currentOrder, provider] });
    }
  };

  const removeProviderFromFallback = (provider) => {
    const currentOrder = routingConfig?.fallback?.fallback_order || [];
    updateFallback({ fallback_order: currentOrder.filter(p => p !== provider) });
  };

  const moveProviderInFallback = (index, direction) => {
    const currentOrder = [...(routingConfig?.fallback?.fallback_order || [])];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= currentOrder.length) return;
    [currentOrder[index], currentOrder[newIndex]] = [currentOrder[newIndex], currentOrder[index]];
    updateFallback({ fallback_order: currentOrder });
  };

  const getAvailableProviders = () => {
    const providerNames = providers.map(p => p.name);
    const defaultProviders = ['openai', 'anthropic', 'google', 'xai', 'meta', 'mistral', 'cohere', 'aws-bedrock', 'azure-openai', 'local-vllm'];
    const configProviders = routingConfig?.fallback?.fallback_order || [];
    const currentDefault = routingConfig?.default_provider ? [routingConfig.default_provider] : [];
    const allProviders = [...new Set([...providerNames, ...defaultProviders, ...configProviders, ...currentDefault])];
    return allProviders.sort();
  };

  const copyProxyUrl = () => {
    navigator.clipboard.writeText(proxyUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleStrategy = (strategyName) => {
    if (!routingConfig) return;
    setRoutingConfig(config => ({
      ...config,
      strategies: config.strategies.map(s => 
        s.name === strategyName ? { ...s, enabled: !s.enabled } : s
      )
    }));
    setHasChanges(true);
  };

  const getProviderIcon = (provider) => {
    const icons = {
      openai: '🤖',
      anthropic: '🧠',
      google: '🔮',
      xai: '✖️',
      meta: '📘',
      mistral: '🌊',
      cohere: '🔷',
      azure: '☁️',
      'azure-openai': '☁️',
      'aws-bedrock': '🟠',
      mock: '🎭',
      local: '💻',
      'local-vllm': '💻',
    };
    return icons[provider.toLowerCase()] || '🔌';
  };

  const getStatusBadge = (status) => {
    if (status === 'active' || status === 'healthy') {
      return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">Active</span>;
    }
    if (status === 'degraded') {
      return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">Degraded</span>;
    }
    return <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">Inactive</span>;
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const fallbackOrder = routingConfig?.fallback?.fallback_order || [];
  const allProviders = getAvailableProviders();
  const unusedProviders = allProviders.filter(p => !fallbackOrder.includes(p));

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Router Configuration" />

      <div className="flex-1 overflow-auto p-4 md:p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <p className="text-gray-600">Configure AI provider routing, fallbacks, rate limits, and load balancing</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={fetchData}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
              >
                <RefreshCw size={18} />
                <span>Refresh</span>
              </button>
              {hasChanges && canEdit && (
                <button
                  onClick={saveConfig}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
                >
                  <Save size={18} />
                  <span>{saving ? 'Saving...' : 'Save Changes'}</span>
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
              <AlertTriangle className="text-red-500" size={20} />
              <span className="text-red-700">{error}</span>
              <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
                <XCircle size={18} />
              </button>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
              <CheckCircle className="text-green-500" size={20} />
              <span className="text-green-700">{success}</span>
            </div>
          )}

          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {['providers', 'api-routes', 'policies', 'settings', 'routing', 'models', 'test'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap min-h-[44px] ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-300'
                }`}
              >
                {tab === 'api-routes' ? 'API Routes' : 
                 tab === 'policies' ? 'Guardrail Profiles' :
                 tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <Server size={24} className="text-gray-700" />
                  <h2 className="text-xl font-bold text-gray-900">Proxy URL</h2>
                </div>
                <p className="text-gray-600 mb-4">Configure your clients to use this URL to route through the AI Gateway</p>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={proxyUrl}
                    readOnly
                    className="flex-1 px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg font-mono text-sm"
                  />
                  <button
                    onClick={copyProxyUrl}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200"
                  >
                    {copied ? <Check size={18} className="text-green-600" /> : <Copy size={18} />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700 mb-2">Python Example:</p>
                  <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
{`from openai import OpenAI

client = OpenAI(
    api_key="your-gateway-api-key",
    base_url="${proxyUrl}"
)`}
                  </pre>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <RotateCcw size={24} className="text-gray-700" />
                  <h2 className="text-xl font-bold text-gray-900">Fallback & Retries</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fallback Enabled</label>
                    <button
                      onClick={() => canEdit && updateFallback({ enabled: !routingConfig?.fallback?.enabled })}
                      disabled={!canEdit}
                      className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                        routingConfig?.fallback?.enabled ? 'bg-green-600' : 'bg-gray-300'
                      } ${!canEdit ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <span
                        className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                          routingConfig?.fallback?.enabled ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      value={routingConfig?.fallback?.max_retries || 2}
                      onChange={(e) => canEdit && updateFallback({ max_retries: parseInt(e.target.value) || 0 })}
                      disabled={!canEdit}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Default Provider</label>
                    <select
                      value={routingConfig?.default_provider || 'openai'}
                      onChange={(e) => canEdit && updateConfig({ default_provider: e.target.value })}
                      disabled={!canEdit}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    >
                      {getAvailableProviders().map(p => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Fallback Order</label>
                  <p className="text-sm text-gray-500 mb-3">Use arrows to reorder providers. Requests will fallback in this order if the primary fails.</p>
                  <div className="space-y-2 mb-4">
                    {fallbackOrder.map((provider, idx) => (
                      <div key={provider} className="flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                        <span className="font-medium text-gray-600 w-6">{idx + 1}.</span>
                        <span className="text-xl">{getProviderIcon(provider)}</span>
                        <span className="capitalize flex-1">{provider}</span>
                        {canEdit && (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => moveProviderInFallback(idx, 'up')}
                              disabled={idx === 0}
                              className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              title="Move up"
                            >
                              <ArrowUp size={16} />
                            </button>
                            <button
                              onClick={() => moveProviderInFallback(idx, 'down')}
                              disabled={idx === fallbackOrder.length - 1}
                              className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              title="Move down"
                            >
                              <ArrowDown size={16} />
                            </button>
                            <button
                              onClick={() => removeProviderFromFallback(provider)}
                              className="p-1 text-gray-400 hover:text-red-600"
                              title="Remove"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                    {fallbackOrder.length === 0 && (
                      <p className="text-sm text-gray-400 italic py-2">No providers in fallback chain. Add providers below.</p>
                    )}
                  </div>

                  {canEdit && unusedProviders.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">Add provider to fallback chain:</p>
                      <div className="flex flex-wrap gap-2">
                        {unusedProviders.map(provider => (
                          <button
                            key={provider}
                            onClick={() => addProviderToFallback(provider)}
                            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 border border-blue-200"
                          >
                            <Plus size={14} />
                            <span>{getProviderIcon(provider)}</span>
                            <span className="capitalize">{provider}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Gauge size={24} className="text-gray-700" />
                    <h2 className="text-xl font-bold text-gray-900">Rate Limits</h2>
                  </div>
                  {canEdit && (
                    <button
                      onClick={addTier}
                      className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
                    >
                      <Plus size={16} />
                      Add Tier
                    </button>
                  )}
                </div>
                
                <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Default Rate Limits</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Requests per minute</label>
                      <input
                        type="number"
                        value={routingConfig?.rate_limits_default?.requests_per_minute || 100}
                        onChange={(e) => canEdit && updateDefaultRateLimits('requests_per_minute', e.target.value)}
                        disabled={!canEdit}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Tokens per minute</label>
                      <input
                        type="number"
                        value={routingConfig?.rate_limits_default?.tokens_per_minute || 100000}
                        onChange={(e) => canEdit && updateDefaultRateLimits('tokens_per_minute', e.target.value)}
                        disabled={!canEdit}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                      />
                    </div>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">Configure rate limit tiers for different user/API key levels</p>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Requests/min</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tokens/min</th>
                        {canEdit && <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {(routingConfig?.rate_limit_tiers || []).map((tier) => (
                        <tr key={tier.name} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            {editingTierName === tier.name ? (
                              <input
                                type="text"
                                value={newTierName}
                                onChange={(e) => setNewTierName(e.target.value)}
                                onBlur={() => renameTier(tier.name, newTierName)}
                                onKeyDown={(e) => e.key === 'Enter' && renameTier(tier.name, newTierName)}
                                autoFocus
                                className="w-32 px-2 py-1 border border-blue-300 rounded focus:ring-2 focus:ring-blue-500"
                              />
                            ) : (
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-1 bg-gray-100 rounded text-sm font-medium capitalize">
                                  {tier.name}
                                </span>
                                {canEdit && (
                                  <button
                                    onClick={() => {
                                      setEditingTierName(tier.name);
                                      setNewTierName(tier.name);
                                    }}
                                    className="p-1 text-gray-400 hover:text-gray-600"
                                  >
                                    <Edit2 size={14} />
                                  </button>
                                )}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              value={tier.requests_per_minute}
                              onChange={(e) => updateTier(tier.name, 'requests_per_minute', e.target.value)}
                              disabled={!canEdit}
                              className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <input
                              type="number"
                              value={tier.tokens_per_minute}
                              onChange={(e) => updateTier(tier.name, 'tokens_per_minute', e.target.value)}
                              disabled={!canEdit}
                              className="w-32 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                            />
                          </td>
                          {canEdit && (
                            <td className="px-4 py-3">
                              <button
                                onClick={() => removeTier(tier.name)}
                                className="p-1 text-gray-400 hover:text-red-600"
                              >
                                <Trash2 size={18} />
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> Rate limiting requires Redis. Set the <code className="bg-blue-100 px-1 rounded">REDIS_URL</code> environment variable to enable rate limiting.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'providers' && (
            <div className="space-y-4">
              <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <GitBranch size={28} className="text-gray-700" />
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">Backend Providers</h2>
                      <p className="text-sm text-gray-600">Configure AI service backends with endpoints, credentials, and models</p>
                    </div>
                  </div>
                  {canEdit && (
                    <button
                      onClick={() => {
                        setEditingProvider(null);
                        setProviderModalOpen(true);
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Plus size={16} />
                      Add Provider
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{providers.length + configuredProviders.length}</p>
                    <p className="text-sm text-gray-500">Total Providers</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{models.length}</p>
                    <p className="text-sm text-gray-500">Models</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-green-600">{providers.filter(p => p.status === 'active').length + configuredProviders.filter(p => p.is_active).length}</p>
                    <p className="text-sm text-gray-500">Active</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{configuredProviders.length}</p>
                    <p className="text-sm text-gray-500">Custom Configured</p>
                  </div>
                </div>
              </div>

              {configuredProviders.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Settings size={18} />
                    Custom Configured Providers
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {configuredProviders.map((provider, idx) => (
                      <div key={idx} className="bg-white rounded-lg shadow border border-gray-200 p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">{getProviderIcon(provider.service_type)}</span>
                            <div>
                              <h3 className="font-semibold">{provider.display_name || provider.name}</h3>
                              <p className="text-xs text-gray-500 capitalize">{provider.service_type}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {provider.is_active ? (
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">Active</span>
                            ) : (
                              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">Inactive</span>
                            )}
                            {canEdit && (
                              <button
                                onClick={() => {
                                  setEditingProvider(provider);
                                  setProviderModalOpen(true);
                                }}
                                className="p-1 text-gray-400 hover:text-blue-600"
                              >
                                <Edit2 size={16} />
                              </button>
                            )}
                          </div>
                        </div>
                        
                        <div className="space-y-2 mb-3 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-gray-500 flex items-center gap-1">
                              <Server size={14} />
                              Endpoint
                            </span>
                            <span className="font-mono text-xs truncate max-w-32" title={provider.endpoint_url}>
                              {provider.endpoint_url ? new URL(provider.endpoint_url).hostname : 'Default'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-gray-500 flex items-center gap-1">
                              <Clock size={14} />
                              Timeout
                            </span>
                            <span>{provider.timeout_seconds}s</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-gray-500 flex items-center gap-1">
                              <Globe size={14} />
                              Traffic
                            </span>
                            <span className={provider.traffic_leaves_enterprise ? 'text-yellow-600' : 'text-green-600'}>
                              {provider.traffic_leaves_enterprise ? 'External' : 'Internal'}
                            </span>
                          </div>
                        </div>

                        <div className="border-t pt-3">
                          <p className="text-xs text-gray-500 mb-2">Models ({provider.models?.length || 0})</p>
                          <div className="flex flex-wrap gap-1">
                            {(provider.models || []).slice(0, 3).map((model, midx) => (
                              <span key={midx} className="text-xs px-2 py-1 bg-gray-100 rounded">
                                {model}
                              </span>
                            ))}
                            {(provider.models || []).length > 3 && (
                              <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                                +{provider.models.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Built-in Providers</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {providers.map((provider, idx) => (
                    <div key={idx} className="bg-white rounded-lg shadow p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{getProviderIcon(provider.name)}</span>
                          <h3 className="font-semibold capitalize">{provider.name}</h3>
                        </div>
                        {getStatusBadge(provider.status)}
                      </div>
                      
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Models</span>
                          <span className="font-medium">{provider.models.length}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Priority</span>
                          <span className="font-medium">{provider.priority}</span>
                        </div>
                      </div>

                      <div className="border-t pt-3">
                        <p className="text-xs text-gray-500 mb-2">Available Models</p>
                        <div className="flex flex-wrap gap-1">
                          {provider.models.slice(0, 3).map((model, midx) => (
                            <span key={midx} className="text-xs px-2 py-1 bg-gray-100 rounded">
                              {typeof model === 'string' ? model : model.id?.split('/').pop() || model}
                            </span>
                          ))}
                          {provider.models.length > 3 && (
                            <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                              +{provider.models.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api-routes' && (
            <div className="space-y-4">
              <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <ArrowRight size={28} className="text-gray-700" />
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">API Routes</h2>
                      <p className="text-sm text-gray-600">Define custom API routes with per-route policies, rate limits, and provider assignments</p>
                    </div>
                  </div>
                  {canEdit && (
                    <button
                      onClick={() => {
                        setEditingRoute(null);
                        setRouteModalOpen(true);
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <Plus size={16} />
                      Add Route
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{apiRoutes.length}</p>
                    <p className="text-sm text-gray-500">Total Routes</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-green-600">{apiRoutes.filter(r => r.is_active).length}</p>
                    <p className="text-sm text-gray-500">Active</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{apiRoutes.filter(r => r.rate_limit_rpm > 0).length}</p>
                    <p className="text-sm text-gray-500">Rate Limited</p>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <p className="text-2xl font-bold text-gray-900">{apiRoutes.filter(r => r.policy_id).length}</p>
                    <p className="text-sm text-gray-500">With Policies</p>
                  </div>
                </div>
              </div>

              {apiRoutes.length === 0 ? (
                <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                  <ArrowRight size={48} className="mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">No Custom Routes</h3>
                  <p className="text-gray-500 mb-4">Create custom API routes to control routing behavior per endpoint</p>
                  {canEdit && (
                    <button
                      onClick={() => {
                        setEditingRoute(null);
                        setRouteModalOpen(true);
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Create First Route
                    </button>
                  )}
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Route</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Methods</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Provider</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Rate Limit</th>
                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Status</th>
                        <th className="text-right px-4 py-3 text-sm font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {apiRoutes.map((route, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900 font-mono text-sm">{route.path}</div>
                            {route.description && (
                              <div className="text-xs text-gray-500">{route.description}</div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              {(route.methods || ['POST']).map((method, midx) => (
                                <span key={midx} className={`text-xs px-2 py-0.5 rounded font-medium ${
                                  method === 'GET' ? 'bg-green-100 text-green-700' :
                                  method === 'POST' ? 'bg-blue-100 text-blue-700' :
                                  method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                                  method === 'DELETE' ? 'bg-red-100 text-red-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {method}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-700 capitalize">{route.default_provider_id ? 'Custom' : 'Default'}</span>
                          </td>
                          <td className="px-4 py-3">
                            {route.rate_limit_rpm > 0 ? (
                              <span className="text-sm text-gray-700">{route.rate_limit_rpm} req/min</span>
                            ) : (
                              <span className="text-sm text-gray-400">None</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {route.is_active ? (
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">Active</span>
                            ) : (
                              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">Inactive</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canEdit && (
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  onClick={() => {
                                    setEditingRoute(route);
                                    setRouteModalOpen(true);
                                  }}
                                  className="p-1 text-gray-400 hover:text-blue-600"
                                >
                                  <Edit2 size={16} />
                                </button>
                                <button
                                  onClick={async () => {
                                    if (confirm('Delete this route?')) {
                                      try {
                                        await api.delete(`/admin/providers/routes/${route.id}`, {
                                          headers: { Authorization: `Bearer ${token}` }
                                        });
                                        fetchData();
                                      } catch (err) {
                                        setError('Failed to delete route');
                                      }
                                    }
                                  }}
                                  className="p-1 text-gray-400 hover:text-red-600"
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-3">Built-in Routes</h3>
                <p className="text-sm text-gray-600 mb-4">These routes are provided by default and cannot be modified</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { path: '/chat/completions', method: 'POST', desc: 'Chat completions API (OpenAI-compatible)' },
                    { path: '/embeddings', method: 'POST', desc: 'Text embeddings API' },
                    { path: '/models', method: 'GET', desc: 'List available models' },
                    { path: '/completions', method: 'POST', desc: 'Text completions API' }
                  ].map((route, idx) => (
                    <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                          route.method === 'GET' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {route.method}
                        </span>
                        <span className="font-mono text-sm font-medium text-gray-900">{route.path}</span>
                      </div>
                      <p className="text-xs text-gray-500">{route.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'policies' && (
            <PolicyDesigner />
          )}

          {activeTab === 'routing' && (
            <div className="space-y-4">
              {routingConfig && (
                <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4 shadow-sm">
                  <h3 className="font-semibold mb-3 text-gray-900">Current Configuration</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <p className="text-sm text-gray-500">Default Provider</p>
                      <p className="font-bold capitalize text-gray-900">{routingConfig.default_provider}</p>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <p className="text-sm text-gray-500">Default Model</p>
                      <p className="font-bold text-gray-900">{routingConfig.default_model}</p>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <p className="text-sm text-gray-500">Fallback</p>
                      <p className="font-bold text-gray-900">{routingConfig.fallback?.enabled ? 'Enabled' : 'Disabled'}</p>
                    </div>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <p className="text-sm text-gray-500">Max Retries</p>
                      <p className="font-bold text-gray-900">{routingConfig.fallback?.max_retries || 2}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-lg shadow p-4 mb-4">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Zap className="text-yellow-500" size={20} />
                  Routing Strategies
                </h3>
                <p className="text-sm text-gray-600">
                  Configure how requests are routed across providers. Multiple strategies can be enabled for different scenarios.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(routingConfig?.strategies || []).map((strategy, idx) => (
                  <div key={idx} className="bg-white rounded-lg shadow p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold capitalize">{strategy.name.replace(/_/g, ' ')}</h4>
                        <p className="text-sm text-gray-600">{strategy.description}</p>
                      </div>
                      <button
                        onClick={() => toggleStrategy(strategy.name)}
                        disabled={!canEdit}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          strategy.enabled ? 'bg-blue-600' : 'bg-gray-200'
                        } ${!canEdit ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            strategy.enabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>

                    <div className="mt-2">
                      <p className="text-xs text-gray-500 mb-1">Priority Order:</p>
                      <div className="flex flex-wrap gap-1">
                        {(strategy.priority_order || []).slice(0, 3).map((model, midx) => (
                          <span key={midx} className="text-xs px-2 py-1 bg-gray-100 rounded">{model}</span>
                        ))}
                        {(strategy.priority_order || []).length > 3 && (
                          <span className="text-xs px-2 py-1 bg-gray-100 rounded">+{strategy.priority_order.length - 3} more</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold">Fallback Chain</h3>
                  <button
                    onClick={checkHealth}
                    disabled={checkingHealth}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100"
                  >
                    <Activity size={16} />
                    {checkingHealth ? 'Checking...' : 'Check Health'}
                  </button>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {(fallbackChain?.chain || []).map((provider, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                        provider.is_active ? 'bg-green-50 border border-green-200' : 'bg-gray-100'
                      }`}>
                        <span>{getProviderIcon(provider.name)}</span>
                        <span className="font-medium capitalize">{provider.name}</span>
                        {!provider.is_active && <span className="text-xs text-gray-500">(inactive)</span>}
                      </div>
                      {idx < (fallbackChain?.chain || []).length - 1 && (
                        <ArrowRight className="text-gray-400" size={20} />
                      )}
                    </div>
                  ))}
                </div>
                {healthChecks.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm font-medium mb-2">Health Status</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {healthChecks.map((check, idx) => (
                        <div key={idx} className={`p-2 rounded-lg text-sm ${
                          check.status === 'healthy' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                        }`}>
                          <div className="flex items-center gap-1">
                            {check.status === 'healthy' ? <CheckCircle size={14} /> : <XCircle size={14} />}
                            <span className="font-medium capitalize">{check.provider}</span>
                          </div>
                          {check.latency_ms && <p className="text-xs mt-1">{check.latency_ms}ms</p>}
                          {check.error && <p className="text-xs mt-1">{check.error}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-sm text-gray-500 mt-3">
                  If primary provider fails, requests automatically route to the next provider in the chain.
                </p>
              </div>

              {routingStats.length > 0 && (
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="font-semibold mb-4">Routing Statistics (Last 7 Days)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {routingStats.map((stat, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <span>{getProviderIcon(stat.provider)}</span>
                          <span className="font-medium capitalize">{stat.provider}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-sm">
                          <div>
                            <p className="text-gray-500">Requests</p>
                            <p className="font-medium">{stat.requests}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Tokens</p>
                            <p className="font-medium">{stat.tokens.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-500">Avg Latency</p>
                            <p className="font-medium">{stat.avg_latency_ms}ms</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'models' && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden md:table-cell">Context</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase hidden lg:table-cell">Pricing</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {models.map((model, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{getProviderIcon(model.provider)}</span>
                            <div>
                              <p className="font-medium text-gray-900">{model.name || model.id}</p>
                              <p className="text-sm text-gray-500 hidden sm:block">{model.id}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="capitalize">{model.provider}</span>
                        </td>
                        <td className="px-4 py-3 hidden md:table-cell">
                          <span className="text-gray-600">{((model.context_length || model.context_window || 0) / 1000).toFixed(0)}K</span>
                        </td>
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <div className="text-sm">
                            <p className="text-gray-600">
                              ₹{((model.input_cost_per_1k || 0) * 83.5).toFixed(4)}/1K in
                            </p>
                            <p className="text-gray-600">
                              ₹{((model.output_cost_per_1k || 0) * 83.5).toFixed(4)}/1K out
                            </p>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {model.is_enabled !== false ? getStatusBadge('active') : getStatusBadge('inactive')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'test' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Play className="text-green-600" size={20} />
                Test Routing
              </h3>
              <p className="text-gray-600 mb-4">
                Test the routing configuration by sending a request to a specific model.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select Model</label>
                  <select
                    value={testModel}
                    onChange={(e) => setTestModel(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Choose a model...</option>
                    {models.map((model, idx) => (
                      <option key={idx} value={model.id}>
                        {getProviderIcon(model.provider)} {model.name || model.id} ({model.provider})
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={testRoute}
                  disabled={!testModel || testing}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Play size={18} />
                  <span>{testing ? 'Testing...' : 'Test Route'}</span>
                </button>

                {testResult && (
                  <div className={`p-4 rounded-lg ${
                    testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    {testResult.success ? (
                      <div className="flex items-start gap-3">
                        <CheckCircle className="text-green-600 mt-0.5" size={20} />
                        <div>
                          <p className="font-medium text-green-800">Routing Successful</p>
                          <p className="text-sm text-green-700 mt-1">
                            Model: {testResult.model} | Provider: {testResult.provider}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start gap-3">
                        <XCircle className="text-red-600 mt-0.5" size={20} />
                        <div>
                          <p className="font-medium text-red-800">Routing Failed</p>
                          <p className="text-sm text-red-700 mt-1">{testResult.error}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <ProviderSetupModal
        isOpen={providerModalOpen}
        onClose={() => {
          setProviderModalOpen(false);
          setEditingProvider(null);
        }}
        onSave={fetchData}
        editProvider={editingProvider}
        token={token}
      />

      <RouteSetupModal
        isOpen={routeModalOpen}
        onClose={() => {
          setRouteModalOpen(false);
          setEditingRoute(null);
        }}
        onSave={fetchData}
        editRoute={editingRoute}
        token={token}
      />
    </div>
  );
}
