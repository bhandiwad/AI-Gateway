import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import InfinitAILogo from './InfinitAILogo';
import { 
  CheckCircle, 
  Circle, 
  ArrowRight, 
  ArrowLeft,
  Key,
  Server,
  Shield,
  Zap,
  Copy,
  Check,
  AlertCircle,
  Sparkles,
  X
} from 'lucide-react';

const STEPS = [
  { id: 'welcome', title: 'Welcome', icon: Sparkles },
  { id: 'provider', title: 'Configure Provider', icon: Server },
  { id: 'apikey', title: 'Create API Key', icon: Key },
  { id: 'test', title: 'Test Connection', icon: Zap },
  { id: 'complete', title: 'Complete', icon: CheckCircle },
];

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', icon: '🤖', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
  { id: 'anthropic', name: 'Anthropic', icon: '🧠', models: ['claude-3-5-sonnet', 'claude-3-opus', 'claude-3-haiku'] },
  { id: 'google', name: 'Google AI', icon: '🔮', models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
  { id: 'xai', name: 'xAI', icon: '✖️', models: ['grok-beta'] },
  { id: 'mistral', name: 'Mistral', icon: '🌊', models: ['mistral-large', 'mistral-medium'] },
];

export default function SetupWizard({ isOpen, onClose, onComplete }) {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [providerApiKey, setProviderApiKey] = useState('');
  const [createdApiKey, setCreatedApiKey] = useState('');
  const [apiKeyName, setApiKeyName] = useState('My First API Key');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const [existingProviders, setExistingProviders] = useState([]);
  const [existingApiKeys, setExistingApiKeys] = useState([]);

  useEffect(() => {
    if (isOpen) {
      checkExistingSetup();
    }
  }, [isOpen]);

  const checkExistingSetup = async () => {
    try {
      const [providersRes, keysRes] = await Promise.all([
        api.get('/admin/providers', { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] })),
        api.get('/admin/api-keys', { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: [] }))
      ]);
      setExistingProviders(providersRes.data || []);
      setExistingApiKeys(keysRes.data || []);
    } catch (err) {
      console.error('Failed to check existing setup:', err);
    }
  };

  const handleProviderSetup = async () => {
    if (!selectedProvider || !providerApiKey) {
      setError('Please select a provider and enter your API key');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.post('/admin/providers', {
        name: selectedProvider.id,
        display_name: selectedProvider.name,
        provider_type: selectedProvider.id,
        api_key: providerApiKey,
        is_active: true,
        models: selectedProvider.models.map(m => ({ id: m, name: m }))
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCurrentStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to configure provider');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!apiKeyName.trim()) {
      setError('Please enter a name for your API key');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/admin/api-keys', {
        name: apiKeyName,
        permissions: ['chat', 'embeddings', 'models']
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCreatedApiKey(response.data.key || response.data.api_key);
      setCurrentStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      const response = await api.post('/chat/completions', {
        model: selectedProvider?.models[0] || 'gpt-4o',
        messages: [{ role: 'user', content: 'Say "Hello from InfinitAI Gateway!" in exactly those words.' }],
        max_tokens: 50
      }, {
        headers: { Authorization: `Bearer ${createdApiKey}` }
      });

      setTestResult({
        success: true,
        message: response.data.choices?.[0]?.message?.content || 'Connection successful!'
      });
      
      setTimeout(() => setCurrentStep(4), 1500);
    } catch (err) {
      setTestResult({
        success: false,
        message: err.response?.data?.detail || 'Connection test failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const copyApiKey = () => {
    navigator.clipboard.writeText(createdApiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleComplete = () => {
    onComplete?.();
    onClose();
    navigate('/playground');
  };

  const skipToStep = (stepIndex) => {
    if (stepIndex <= currentStep) {
      setCurrentStep(stepIndex);
    }
  };

  if (!isOpen) return null;

  const step = STEPS[currentStep];

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700">
          <div className="flex items-center gap-4">
            <InfinitAILogo className="w-10 h-10" />
            <div className="text-white">
              <h2 className="text-xl font-bold">Setup Wizard</h2>
              <p className="text-blue-100 text-sm">Get started with InfinitAI Gateway</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <div className="flex items-center justify-center gap-2 py-4 px-6 bg-gray-50 border-b overflow-x-auto">
          {STEPS.map((s, idx) => (
            <button
              key={s.id}
              onClick={() => skipToStep(idx)}
              disabled={idx > currentStep}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                idx === currentStep
                  ? 'bg-blue-600 text-white'
                  : idx < currentStep
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              {idx < currentStep ? (
                <CheckCircle size={16} />
              ) : (
                <s.icon size={16} />
              )}
              <span className="hidden sm:inline">{s.title}</span>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
              <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
              <p className="text-red-700 text-sm">{error}</p>
              <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
                <X size={18} />
              </button>
            </div>
          )}

          {currentStep === 0 && (
            <div className="text-center py-8">
              <Sparkles size={64} className="mx-auto text-blue-600 mb-6" />
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Welcome to InfinitAI Gateway!</h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                This wizard will help you set up your first AI provider and API key in just a few steps.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 max-w-2xl mx-auto">
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <Server size={32} className="text-blue-600 mx-auto mb-3" />
                  <h4 className="font-semibold text-gray-900">Multi-Provider</h4>
                  <p className="text-sm text-gray-500">Connect OpenAI, Anthropic, Google, and more</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <Shield size={32} className="text-green-600 mx-auto mb-3" />
                  <h4 className="font-semibold text-gray-900">Guardrails</h4>
                  <p className="text-sm text-gray-500">Content filtering and safety controls</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <Zap size={32} className="text-amber-600 mx-auto mb-3" />
                  <h4 className="font-semibold text-gray-900">Smart Routing</h4>
                  <p className="text-sm text-gray-500">Automatic failover and load balancing</p>
                </div>
              </div>

              {existingProviders.length > 0 && (
                <div className="mb-6 p-4 bg-lime-50 border border-lime-200 rounded-lg">
                  <p className="text-lime-800">
                    <CheckCircle size={16} className="inline mr-2" />
                    You already have {existingProviders.length} provider(s) configured. 
                    {existingApiKeys.length > 0 && ` and ${existingApiKeys.length} API key(s).`}
                  </p>
                </div>
              )}
            </div>
          )}

          {currentStep === 1 && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Configure Your First Provider</h3>
              <p className="text-gray-600 mb-6">Select an AI provider and enter your API key to get started.</p>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                {PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      selectedProvider?.id === provider.id
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <span className="text-2xl mb-2 block">{provider.icon}</span>
                    <span className="font-semibold text-gray-900">{provider.name}</span>
                  </button>
                ))}
              </div>

              {selectedProvider && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {selectedProvider.name} API Key
                    </label>
                    <input
                      type="password"
                      value={providerApiKey}
                      onChange={(e) => setProviderApiKey(e.target.value)}
                      placeholder={`Enter your ${selectedProvider.name} API key`}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      Get your API key from the {selectedProvider.name} dashboard
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Available Models:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedProvider.models.map((model) => (
                        <span key={model} className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-700">
                          {model}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {currentStep === 2 && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Create Your API Key</h3>
              <p className="text-gray-600 mb-6">Create an API key to authenticate your requests to the gateway.</p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">API Key Name</label>
                  <input
                    type="text"
                    value={apiKeyName}
                    onChange={(e) => setApiKeyName(e.target.value)}
                    placeholder="e.g., Development Key"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <p className="text-sm text-amber-800">
                    <AlertCircle size={16} className="inline mr-2" />
                    Keep your API key secure! It will only be shown once after creation.
                  </p>
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Test Your Connection</h3>
              <p className="text-gray-600 mb-6">Your API key has been created. Save it now, then test the connection.</p>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Your API Key</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={createdApiKey}
                    readOnly
                    className="flex-1 px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg font-mono text-sm"
                  />
                  <button
                    onClick={copyApiKey}
                    className="px-4 py-3 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200"
                  >
                    {copied ? <Check size={20} className="text-green-600" /> : <Copy size={20} />}
                  </button>
                </div>
                <p className="text-xs text-red-600 mt-2 font-medium">
                  ⚠️ Save this key now! It won't be shown again.
                </p>
              </div>

              {testResult && (
                <div className={`mb-6 p-4 rounded-lg border ${
                  testResult.success 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center gap-3">
                    {testResult.success ? (
                      <CheckCircle className="text-green-600" size={24} />
                    ) : (
                      <AlertCircle className="text-red-600" size={24} />
                    )}
                    <div>
                      <p className={`font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                        {testResult.success ? 'Connection Successful!' : 'Connection Failed'}
                      </p>
                      <p className={`text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                        {testResult.message}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {currentStep === 4 && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle size={48} className="text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">You're All Set!</h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Your AI Gateway is now configured and ready to use. Head to the Playground to start making requests!
              </p>
              
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 max-w-md mx-auto text-left">
                <h4 className="font-semibold text-gray-900 mb-3">Quick Start</h4>
                <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
{`from openai import OpenAI

client = OpenAI(
    api_key="${createdApiKey.substring(0, 20)}...",
    base_url="${window.location.origin}/api/v1"
)

response = client.chat.completions.create(
    model="${selectedProvider?.models[0] || 'gpt-4o'}",
    messages=[{"role": "user", "content": "Hello!"}]
)`}
                </pre>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div>
            {currentStep > 0 && currentStep < 4 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                <ArrowLeft size={18} />
                Back
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {currentStep === 0 && (
              <>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Skip for now
                </button>
                <button
                  onClick={() => setCurrentStep(1)}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Get Started
                  <ArrowRight size={18} />
                </button>
              </>
            )}
            
            {currentStep === 1 && (
              <button
                onClick={handleProviderSetup}
                disabled={loading || !selectedProvider || !providerApiKey}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Configuring...' : 'Configure Provider'}
                <ArrowRight size={18} />
              </button>
            )}
            
            {currentStep === 2 && (
              <button
                onClick={handleCreateApiKey}
                disabled={loading || !apiKeyName.trim()}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create API Key'}
                <ArrowRight size={18} />
              </button>
            )}
            
            {currentStep === 3 && (
              <button
                onClick={handleTestConnection}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Test Connection'}
                <Zap size={18} />
              </button>
            )}
            
            {currentStep === 4 && (
              <button
                onClick={handleComplete}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Go to Playground
                <ArrowRight size={18} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
