import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Plus, Edit2, Trash2, TestTube, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI Moderation', description: 'Hate speech, toxicity, self-harm, sexual content, violence' },
  { value: 'aws_comprehend', label: 'AWS Comprehend', description: 'PII detection, sentiment analysis, toxicity' },
  { value: 'google_nlp', label: 'Google Cloud NLP', description: 'Sentiment analysis, content classification' },
  { value: 'azure_content_safety', label: 'Azure Content Safety', description: 'Hate, self-harm, sexual, violence detection' },
];

export default function ExternalGuardrails() {
  const { user } = useAuth();
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [showTestModal, setShowTestModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [testingProvider, setTestingProvider] = useState(null);
  const [healthStatus, setHealthStatus] = useState({});

  useEffect(() => {
    loadProviders();
    loadHealthStatus();
  }, []);

  const loadProviders = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/admin/guardrails/external/providers', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProviders(data);
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHealthStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/admin/guardrails/external/providers/health/all', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const statusMap = {};
        data.forEach(item => {
          statusMap[item.provider_name] = item.is_healthy;
        });
        setHealthStatus(statusMap);
      }
    } catch (error) {
      console.error('Failed to load health status:', error);
    }
  };

  const createProvider = async (data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/admin/guardrails/external/providers', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadProviders();
        await loadHealthStatus();
        setShowProviderModal(false);
        setEditingProvider(null);
      } else {
        const error = await response.json();
        alert(`Failed to create provider: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to create provider:', error);
      alert('Failed to create provider');
    }
  };

  const updateProvider = async (id, data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/guardrails/external/providers/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadProviders();
        setShowProviderModal(false);
        setEditingProvider(null);
      }
    } catch (error) {
      console.error('Failed to update provider:', error);
    }
  };

  const deleteProvider = async (id) => {
    if (!confirm('Are you sure you want to delete this provider?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/guardrails/external/providers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadProviders();
      }
    } catch (error) {
      console.error('Failed to delete provider:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">External Guardrail Providers</h1>
          <p className="text-gray-600 mt-1">Integrate 3rd party guardrail services for enhanced content safety</p>
        </div>

        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Configured Providers</h2>
              <button
                onClick={() => {
                  setEditingProvider(null);
                  setShowProviderModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Provider
              </button>
            </div>

            {providers.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Shield className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No external providers configured</p>
                <button
                  onClick={() => setShowProviderModal(true)}
                  className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Add your first provider
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {providers.map((provider) => (
                  <ProviderCard
                    key={provider.id}
                    provider={provider}
                    healthStatus={healthStatus[provider.name]}
                    onEdit={() => {
                      setEditingProvider(provider);
                      setShowProviderModal(true);
                    }}
                    onDelete={() => deleteProvider(provider.id)}
                    onTest={() => {
                      setTestingProvider(provider);
                      setShowTestModal(true);
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Available Providers Info */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h2 className="text-lg font-semibold mb-4">Available Provider Types</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PROVIDER_TYPES.map((type) => (
                <div key={type.value} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">{type.label}</h3>
                  <p className="text-sm text-gray-600">{type.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Provider Modal */}
      {showProviderModal && (
        <ProviderModal
          provider={editingProvider}
          onClose={() => {
            setShowProviderModal(false);
            setEditingProvider(null);
          }}
          onSave={(data) => {
            if (editingProvider) {
              updateProvider(editingProvider.id, data);
            } else {
              createProvider(data);
            }
          }}
        />
      )}

      {/* Test Modal */}
      {showTestModal && testingProvider && (
        <TestModal
          provider={testingProvider}
          onClose={() => {
            setShowTestModal(false);
            setTestingProvider(null);
          }}
        />
      )}
    </div>
  );
}

function ProviderCard({ provider, healthStatus, onEdit, onDelete, onTest }) {
  const providerType = PROVIDER_TYPES.find(t => t.value === provider.provider_type);
  
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{provider.name}</h3>
            {healthStatus !== undefined && (
              healthStatus ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <XCircle className="w-4 h-4 text-red-600" />
              )
            )}
          </div>
          <p className="text-sm text-gray-500">{providerType?.label}</p>
        </div>
        <div className="flex gap-1">
          <button
            onClick={onTest}
            className="p-1 text-gray-600 hover:text-blue-600"
            title="Test provider"
          >
            <TestTube className="w-4 h-4" />
          </button>
          <button
            onClick={onEdit}
            className="p-1 text-gray-600 hover:text-blue-600"
            title="Edit provider"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-600 hover:text-red-600"
            title="Delete provider"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {provider.description && (
        <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
      )}

      <div className="flex items-center gap-2 mb-2">
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          provider.is_enabled
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {provider.is_enabled ? 'Enabled' : 'Disabled'}
        </span>
        {provider.is_global && (
          <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
            Global
          </span>
        )}
      </div>

      {provider.capabilities && provider.capabilities.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Capabilities</p>
          <div className="flex flex-wrap gap-1">
            {provider.capabilities.slice(0, 3).map((cap) => (
              <span key={cap} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                {cap}
              </span>
            ))}
            {provider.capabilities.length > 3 && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                +{provider.capabilities.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      {provider.total_requests > 0 && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div>
            <p className="text-gray-500">Requests</p>
            <p className="font-medium">{provider.total_requests}</p>
          </div>
          <div>
            <p className="text-gray-500">Avg Latency</p>
            <p className="font-medium">{provider.avg_latency_ms || 0}ms</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ProviderModal({ provider, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: provider?.name || '',
    provider_type: provider?.provider_type || 'openai',
    description: provider?.description || '',
    api_key: '',
    api_endpoint: provider?.api_endpoint || '',
    region: provider?.region || '',
    timeout_seconds: provider?.timeout_seconds || 10,
    retry_attempts: provider?.retry_attempts || 2,
    priority: provider?.priority || 100,
    is_global: provider?.is_global || false,
    thresholds: provider?.thresholds || {
      toxicity: 0.7,
      hate_speech: 0.7,
      violence: 0.7,
      sexual: 0.7,
      self_harm: 0.7
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...formData };
    data.timeout_seconds = parseInt(data.timeout_seconds);
    data.retry_attempts = parseInt(data.retry_attempts);
    data.priority = parseInt(data.priority);
    
    // Convert thresholds to floats
    Object.keys(data.thresholds).forEach(key => {
      data.thresholds[key] = parseFloat(data.thresholds[key]);
    });
    
    // Don't send api_key if it's empty (for updates)
    if (!data.api_key) {
      delete data.api_key;
    }
    
    onSave(data);
  };

  const selectedType = PROVIDER_TYPES.find(t => t.value === formData.provider_type);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">
            {provider ? 'Edit Provider' : 'Add Guardrail Provider'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider Type *
              </label>
              <select
                required
                value={formData.provider_type}
                onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!!provider}
              >
                {PROVIDER_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {selectedType && (
                <p className="mt-1 text-sm text-gray-500">{selectedType.description}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Production OpenAI Moderation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key {!provider && '*'}
              </label>
              <input
                type="password"
                required={!provider}
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder={provider ? "Leave empty to keep existing key" : "Enter API key"}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Endpoint
                </label>
                <input
                  type="url"
                  value={formData.api_endpoint}
                  onChange={(e) => setFormData({ ...formData, api_endpoint: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Optional custom endpoint"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Region
                </label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., us-east-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeout (sec)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Retries
                </label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={formData.retry_attempts}
                  onChange={(e) => setFormData({ ...formData, retry_attempts: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Detection Thresholds (0.0 - 1.0)
              </label>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(formData.thresholds).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-xs text-gray-600 mb-1 capitalize">
                      {key.replace('_', ' ')}
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      value={value}
                      onChange={(e) => setFormData({
                        ...formData,
                        thresholds: {
                          ...formData.thresholds,
                          [key]: e.target.value
                        }
                      })}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_global"
                checked={formData.is_global}
                onChange={(e) => setFormData({ ...formData, is_global: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_global" className="text-sm text-gray-700">
                Global provider (available to all tenants)
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {provider ? 'Update' : 'Create'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TestModal({ provider, onClose }) {
  const [testText, setTestText] = useState('');
  const [testStage, setTestStage] = useState('input');
  const [result, setResult] = useState(null);
  const [testing, setTesting] = useState(false);

  const runTest = async () => {
    if (!testText.trim()) {
      alert('Please enter some text to test');
      return;
    }

    setTesting(true);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/guardrails/external/providers/${provider.id}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: testText,
          stage: testStage
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        const error = await response.json();
        alert(`Test failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Test failed:', error);
      alert('Test failed');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Test {provider.name}</h2>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stage
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="input"
                  checked={testStage === 'input'}
                  onChange={(e) => setTestStage(e.target.value)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm">Input (User prompt)</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="output"
                  checked={testStage === 'output'}
                  onChange={(e) => setTestStage(e.target.value)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm">Output (AI response)</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Test Text
            </label>
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter text to test for violations..."
            />
          </div>

          <button
            onClick={runTest}
            disabled={testing || !testText.trim()}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {testing ? (
              <>
                <Clock className="w-4 h-4 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <TestTube className="w-4 h-4" />
                Run Test
              </>
            )}
          </button>

          {result && (
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center gap-2 mb-3">
                {result.passed ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                )}
                <h3 className="font-semibold">
                  {result.passed ? 'Test Passed' : 'Violations Detected'}
                </h3>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Provider:</span>
                  <span className="font-medium">{result.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Action:</span>
                  <span className={`font-medium ${
                    result.recommended_action === 'block' ? 'text-red-600' :
                    result.recommended_action === 'warn' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {result.recommended_action.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Processing Time:</span>
                  <span className="font-medium">{result.processing_time_ms.toFixed(2)}ms</span>
                </div>
              </div>

              {result.violations && result.violations.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium text-sm mb-2">Violations:</h4>
                  <div className="space-y-2">
                    {result.violations.map((violation, idx) => (
                      <div key={idx} className="bg-white border border-gray-200 rounded p-3">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-sm capitalize">{violation.category}</span>
                          <span className="text-xs text-gray-500">
                            Severity: {(violation.severity * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">{violation.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
