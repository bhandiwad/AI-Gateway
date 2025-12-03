import { useState, useEffect } from 'react';
import { X, Server, Key, Clock, Globe, Shield, Plus, Trash2, ChevronRight, ChevronLeft, Check, AlertTriangle } from 'lucide-react';
import api from '../api/client';

const SERVICE_TYPES = [
  { id: 'openai', name: 'OpenAI', description: 'OpenAI GPT models', icon: '🤖' },
  { id: 'anthropic', name: 'Anthropic', description: 'Claude models', icon: '🧠' },
  { id: 'google', name: 'Google AI', description: 'Gemini models', icon: '🔮' },
  { id: 'azure', name: 'Azure OpenAI', description: 'Azure-hosted OpenAI', icon: '☁️' },
  { id: 'aws-bedrock', name: 'AWS Bedrock', description: 'AWS Bedrock models', icon: '📦' },
  { id: 'mistral', name: 'Mistral AI', description: 'Mistral models', icon: '💨' },
  { id: 'cohere', name: 'Cohere', description: 'Cohere models', icon: '🔗' },
  { id: 'xai', name: 'xAI (Grok)', description: 'Grok models from xAI', icon: '🚀' },
  { id: 'meta', name: 'Meta Llama', description: 'Meta Llama models', icon: '🦙' },
  { id: 'local-vllm', name: 'Local vLLM', description: 'Self-hosted vLLM', icon: '🖥️' },
  { id: 'local-ollama', name: 'Local Ollama', description: 'Self-hosted Ollama', icon: '🦙' },
  { id: 'custom', name: 'Custom Endpoint', description: 'OpenAI-compatible endpoint', icon: '⚙️' },
];

const DEFAULT_ENDPOINTS = {
  'openai': 'https://api.openai.com/v1',
  'anthropic': 'https://api.anthropic.com/v1',
  'google': 'https://generativelanguage.googleapis.com/v1',
  'azure': 'https://your-resource.openai.azure.com/',
  'aws-bedrock': 'https://bedrock.us-east-1.amazonaws.com',
  'mistral': 'https://api.mistral.ai/v1',
  'cohere': 'https://api.cohere.ai/v1',
  'xai': 'https://api.x.ai/v1',
  'meta': 'https://llama-api.meta.com/v1',
  'local-vllm': 'http://localhost:8000/v1',
  'local-ollama': 'http://localhost:11434/api',
  'custom': '',
};

const DEFAULT_MODELS = {
  'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
  'google': ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  'azure': [],
  'aws-bedrock': ['anthropic.claude-3-5-sonnet-20241022-v2:0', 'amazon.titan-text-premier-v1:0'],
  'mistral': ['mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest'],
  'cohere': ['command-r-plus', 'command-r', 'command-light'],
  'xai': ['grok-2', 'grok-2-mini'],
  'meta': ['llama-3.2-90b', 'llama-3.1-70b', 'llama-3.1-8b'],
  'local-vllm': [],
  'local-ollama': [],
  'custom': [],
};

export default function ProviderSetupModal({ isOpen, onClose, onSave, editProvider, token }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    service_type: '',
    endpoint_url: '',
    api_key_secret_name: '',
    timeout_seconds: 120,
    max_retries: 3,
    traffic_leaves_enterprise: true,
    models: [],
    rate_limit_rpm: null,
    rate_limit_tpm: null,
    priority: 0,
    config: {}
  });
  
  const [newModel, setNewModel] = useState('');

  useEffect(() => {
    if (editProvider) {
      setFormData({
        name: editProvider.name || '',
        display_name: editProvider.display_name || '',
        description: editProvider.description || '',
        service_type: editProvider.service_type || '',
        endpoint_url: editProvider.endpoint_url || '',
        api_key_secret_name: editProvider.api_key_secret_name || '',
        timeout_seconds: editProvider.timeout_seconds || 120,
        max_retries: editProvider.max_retries || 3,
        traffic_leaves_enterprise: editProvider.traffic_leaves_enterprise ?? true,
        models: editProvider.models || [],
        rate_limit_rpm: editProvider.rate_limit_rpm || null,
        rate_limit_tpm: editProvider.rate_limit_tpm || null,
        priority: editProvider.priority || 0,
        config: editProvider.config || {}
      });
      setStep(2);
    } else {
      setFormData({
        name: '',
        display_name: '',
        description: '',
        service_type: '',
        endpoint_url: '',
        api_key_secret_name: '',
        timeout_seconds: 120,
        max_retries: 3,
        traffic_leaves_enterprise: true,
        models: [],
        rate_limit_rpm: null,
        rate_limit_tpm: null,
        priority: 0,
        config: {}
      });
      setStep(1);
    }
    setError(null);
  }, [editProvider, isOpen]);

  const handleServiceTypeSelect = (serviceType) => {
    setFormData(prev => ({
      ...prev,
      service_type: serviceType,
      endpoint_url: DEFAULT_ENDPOINTS[serviceType] || '',
      models: DEFAULT_MODELS[serviceType] || [],
      name: prev.name || serviceType,
      display_name: prev.display_name || SERVICE_TYPES.find(s => s.id === serviceType)?.name || serviceType
    }));
    setStep(2);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addModel = () => {
    if (newModel.trim() && !formData.models.includes(newModel.trim())) {
      setFormData(prev => ({
        ...prev,
        models: [...prev.models, newModel.trim()]
      }));
      setNewModel('');
    }
  };

  const removeModel = (model) => {
    setFormData(prev => ({
      ...prev,
      models: prev.models.filter(m => m !== model)
    }));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      const payload = {
        ...formData,
        rate_limit_rpm: formData.rate_limit_rpm || null,
        rate_limit_tpm: formData.rate_limit_tpm || null,
      };

      if (editProvider) {
        await api.put(`/admin/providers/${editProvider.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/admin/providers', payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      onSave();
      onClose();
    } catch (err) {
      console.error('Failed to save provider:', err);
      setError(err.response?.data?.detail || 'Failed to save provider configuration');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const selectedServiceType = SERVICE_TYPES.find(s => s.id === formData.service_type);
  const requiresApiKey = !['local-vllm', 'local-ollama'].includes(formData.service_type);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b bg-gray-50">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {editProvider ? 'Edit Provider' : 'Add Backend Provider'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {step === 1 ? 'Step 1: Select Service Type' : 
               step === 2 ? 'Step 2: Configure Connection' : 
               'Step 3: Define Models'}
            </p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <div className="flex items-center justify-center py-4 border-b bg-gray-50">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {step > s ? <Check size={16} /> : s}
              </div>
              {s < 3 && (
                <div className={`w-16 h-1 mx-2 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
              <AlertTriangle size={20} />
              {error}
            </div>
          )}

          {step === 1 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {SERVICE_TYPES.map((service) => (
                <button
                  key={service.id}
                  onClick={() => handleServiceTypeSelect(service.id)}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 text-left transition-all"
                >
                  <div className="text-2xl mb-2">{service.icon}</div>
                  <h3 className="font-semibold text-gray-900">{service.name}</h3>
                  <p className="text-sm text-gray-500">{service.description}</p>
                </button>
              ))}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-2xl">{selectedServiceType?.icon}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedServiceType?.name}</h3>
                  <p className="text-sm text-gray-500">{selectedServiceType?.description}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Provider Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="e.g., openai-primary"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    value={formData.display_name}
                    onChange={(e) => handleChange('display_name', e.target.value)}
                    placeholder="e.g., OpenAI Primary"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Server size={16} className="inline mr-1" />
                  Endpoint URL
                </label>
                <input
                  type="text"
                  value={formData.endpoint_url}
                  onChange={(e) => handleChange('endpoint_url', e.target.value)}
                  placeholder="https://api.example.com/v1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to use the default endpoint for {selectedServiceType?.name}
                </p>
              </div>

              {requiresApiKey && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Key size={16} className="inline mr-1" />
                    API Key Secret Name
                  </label>
                  <input
                    type="text"
                    value={formData.api_key_secret_name}
                    onChange={(e) => handleChange('api_key_secret_name', e.target.value)}
                    placeholder="e.g., OPENAI_API_KEY"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Name of the environment variable or secret containing the API key
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Clock size={16} className="inline mr-1" />
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={formData.timeout_seconds}
                    onChange={(e) => handleChange('timeout_seconds', parseInt(e.target.value) || 120)}
                    min={1}
                    max={600}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
                  <input
                    type="number"
                    value={formData.max_retries}
                    onChange={(e) => handleChange('max_retries', parseInt(e.target.value) || 3)}
                    min={0}
                    max={10}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rate Limit (requests/min)
                  </label>
                  <input
                    type="number"
                    value={formData.rate_limit_rpm || ''}
                    onChange={(e) => handleChange('rate_limit_rpm', e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="Optional"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <input
                    type="number"
                    value={formData.priority}
                    onChange={(e) => handleChange('priority', parseInt(e.target.value) || 0)}
                    min={0}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Lower = higher priority</p>
                </div>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.traffic_leaves_enterprise}
                    onChange={(e) => handleChange('traffic_leaves_enterprise', e.target.checked)}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <Globe size={16} className="text-gray-500" />
                      <span className="font-medium text-gray-900">Traffic Leaves Enterprise</span>
                    </div>
                    <p className="text-sm text-gray-500">
                      Uncheck for on-premises or VPC-only deployments
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Shield size={16} className="inline mr-1" />
                  Available Models
                </label>
                <p className="text-sm text-gray-500 mb-4">
                  Define which models are available through this provider
                </p>
                
                <div className="flex gap-2 mb-4">
                  <input
                    type="text"
                    value={newModel}
                    onChange={(e) => setNewModel(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addModel()}
                    placeholder="Enter model ID (e.g., gpt-4o)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={addModel}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                  >
                    <Plus size={16} />
                    Add
                  </button>
                </div>

                <div className="border border-gray-200 rounded-lg divide-y max-h-64 overflow-y-auto">
                  {formData.models.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                      No models defined. Add models above or they will be auto-discovered.
                    </div>
                  ) : (
                    formData.models.map((model, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 hover:bg-gray-50">
                        <span className="font-mono text-sm">{model}</span>
                        <button
                          onClick={() => removeModel(model)}
                          className="p-1 text-gray-400 hover:text-red-600"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Optional description for this provider configuration"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div>
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 flex items-center gap-2"
              >
                <ChevronLeft size={16} />
                Back
              </button>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-900"
            >
              Cancel
            </button>
            {step < 3 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={step === 1 && !formData.service_type}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                Next
                <ChevronRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading || !formData.name}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? 'Saving...' : (editProvider ? 'Update Provider' : 'Create Provider')}
                <Check size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
