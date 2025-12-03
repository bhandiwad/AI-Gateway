import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { 
  GitBranch, 
  Server, 
  Zap, 
  RefreshCw, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Settings,
  Save,
  Play,
  ArrowRight,
  Clock,
  DollarSign,
  Activity
} from 'lucide-react';

export default function RouterConfig() {
  const { token } = useAuth();
  const [providers, setProviders] = useState([]);
  const [routingConfig, setRoutingConfig] = useState(null);
  const [fallbackChain, setFallbackChain] = useState(null);
  const [routingStats, setRoutingStats] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('providers');
  const [testModel, setTestModel] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [healthChecks, setHealthChecks] = useState([]);
  const [checkingHealth, setCheckingHealth] = useState(false);

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [providersRes, configRes, fallbackRes, modelsRes, statsRes] = await Promise.all([
        api.get('/admin/router/providers', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/config', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/fallback-chain', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/models', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/router/stats', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: { stats: [] } }))
      ]);

      setProviders(providersRes.data.providers || []);
      setRoutingConfig(configRes.data);
      setFallbackChain(fallbackRes.data);
      setModels(modelsRes.data.data || []);
      setRoutingStats(statsRes.data.stats || []);

    } catch (err) {
      console.error('Failed to fetch router config:', err);
      setError('Failed to load router configuration');
    } finally {
      setLoading(false);
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

  const toggleStrategy = (strategyName) => {
    if (!routingConfig) return;
    setRoutingConfig(config => ({
      ...config,
      strategies: config.strategies.map(s => 
        s.name === strategyName ? { ...s, enabled: !s.enabled } : s
      )
    }));
  };

  const getProviderIcon = (provider) => {
    const icons = {
      openai: '🤖',
      anthropic: '🧠',
      google: '🔮',
      mock: '🎭',
      local: '💻',
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

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Router Configuration</h1>
            <p className="text-gray-600 mt-1">Configure AI provider routing, fallbacks, and load balancing</p>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
          >
            <RefreshCw size={18} />
            <span>Refresh</span>
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['providers', 'routing', 'models', 'test'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap min-h-[44px] ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'providers' && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-6 text-white mb-6">
              <div className="flex items-center gap-3 mb-2">
                <GitBranch size={28} />
                <h2 className="text-xl font-bold">Multi-Provider Gateway</h2>
              </div>
              <p className="text-indigo-100">
                Route requests across multiple AI providers with automatic fallback and load balancing.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{providers.length}</p>
                  <p className="text-sm text-indigo-100">Providers</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{models.length}</p>
                  <p className="text-sm text-indigo-100">Models</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{providers.filter(p => p.status === 'active').length}</p>
                  <p className="text-sm text-indigo-100">Active</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{(routingConfig?.strategies || []).filter(r => r.enabled).length}</p>
                  <p className="text-sm text-indigo-100">Strategies Active</p>
                </div>
              </div>
            </div>

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
        )}

        {activeTab === 'routing' && (
          <div className="space-y-4">
            {routingConfig && (
              <div className="bg-gradient-to-r from-green-600 to-teal-600 rounded-lg p-6 text-white mb-4">
                <h3 className="font-semibold mb-3">Current Configuration</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white/10 rounded-lg p-3">
                    <p className="text-sm text-green-100">Default Provider</p>
                    <p className="font-bold capitalize">{routingConfig.default_provider}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-3">
                    <p className="text-sm text-green-100">Default Model</p>
                    <p className="font-bold">{routingConfig.default_model}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-3">
                    <p className="text-sm text-green-100">Fallback</p>
                    <p className="font-bold">{routingConfig.fallback?.enabled ? 'Enabled' : 'Disabled'}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-3">
                    <p className="text-sm text-green-100">Max Retries</p>
                    <p className="font-bold">{routingConfig.fallback?.max_retries || 2}</p>
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
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        strategy.enabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
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
                            <p className="font-medium text-gray-900">{model.id}</p>
                            <p className="text-sm text-gray-500 hidden sm:block">{model.description || 'AI language model'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="capitalize">{model.provider}</span>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-gray-600">{model.context_window?.toLocaleString() || 'N/A'}</span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <div className="text-sm">
                          <p className="text-gray-600">
                            ${model.input_cost_per_1k || '0.00'}/1K in
                          </p>
                          <p className="text-gray-600">
                            ${model.output_cost_per_1k || '0.00'}/1K out
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {getStatusBadge('active')}
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
                      {model.id} ({model.provider})
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={testRoute}
                disabled={testing || !testModel}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
              >
                <Play size={18} />
                <span>{testing ? 'Testing...' : 'Test Route'}</span>
              </button>

              {testResult && (
                <div className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {testResult.success ? (
                      <>
                        <CheckCircle className="text-green-600" size={24} />
                        <span className="font-semibold text-green-800">Route successful</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="text-red-600" size={24} />
                        <span className="font-semibold text-red-800">Route failed</span>
                      </>
                    )}
                  </div>

                  {testResult.success ? (
                    <div className="grid grid-cols-3 gap-4 mt-3">
                      <div>
                        <p className="text-sm text-gray-500">Model</p>
                        <p className="font-medium">{testResult.model}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Provider</p>
                        <p className="font-medium capitalize">{testResult.provider}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Status</p>
                        <p className="font-medium text-green-600">Connected</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-red-700">{testResult.error}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
