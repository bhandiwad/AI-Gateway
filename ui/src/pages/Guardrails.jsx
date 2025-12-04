import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import Header from '../components/Header';
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Play,
  RefreshCw,
  Info,
  Settings,
  Save,
  Plus,
  Edit2,
  Trash2,
  ExternalLink,
  ChevronRight,
  Layers,
  TestTube,
  Globe
} from 'lucide-react';

const PROVIDER_TYPES = [
  { value: 'openai', label: 'OpenAI Moderation', description: 'Hate speech, toxicity, self-harm, sexual content, violence' },
  { value: 'aws_comprehend', label: 'AWS Comprehend', description: 'PII detection, sentiment analysis, toxicity' },
  { value: 'google_nlp', label: 'Google Cloud NLP', description: 'Sentiment analysis, content classification' },
  { value: 'azure_content_safety', label: 'Azure Content Safety', description: 'Hate, self-harm, sexual, violence detection' },
];

export default function Guardrails() {
  const { token, hasPermission } = useAuth();
  const [guardrails, setGuardrails] = useState([]);
  const [enterpriseInfo, setEnterpriseInfo] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [externalProviders, setExternalProviders] = useState([]);
  const [healthStatus, setHealthStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('strict');
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [showTestModal, setShowTestModal] = useState(false);
  const [testingProvider, setTestingProvider] = useState(null);

  const canEdit = hasPermission('guardrails:edit');

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [guardrailsRes, enterpriseRes, policiesRes, profilesRes] = await Promise.all([
        api.get('/admin/guardrails', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/guardrails/bfsi', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/guardrails/policies', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/providers/profiles/list', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] }))
      ]);

      setGuardrails(guardrailsRes.data.guardrails || []);
      setEnterpriseInfo(enterpriseRes.data);
      setPolicies(policiesRes.data.policies || []);
      setProfiles(profilesRes.data || []);
      
      await loadExternalProviders();
      await loadHealthStatus();
    } catch (err) {
      console.error('Failed to fetch guardrails:', err);
      setError('Failed to load guardrails configuration');
    } finally {
      setLoading(false);
    }
  };

  const loadExternalProviders = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setExternalProviders(data);
      }
    } catch (error) {
      console.error('Failed to load external providers:', error);
    }
  };

  const loadHealthStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers/health/all`, {
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

  const testGuardrails = async () => {
    if (!testInput.trim()) return;

    try {
      setTesting(true);
      setTestResult(null);

      const response = await api.post('/admin/guardrails/test', {
        text: testInput,
        check_types: ['pii', 'toxicity', 'prompt_injection', 'jailbreak']
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setTestResult(response.data);
    } catch (err) {
      console.error('Guardrail test failed:', err);
      setError('Failed to test guardrails');
    } finally {
      setTesting(false);
    }
  };

  const updatePolicy = async () => {
    try {
      setSaving(true);
      await api.put('/admin/guardrails/policy', {
        policy: selectedPolicy
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setError(null);
    } catch (err) {
      console.error('Failed to update policy:', err);
      setError('Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  const deleteProfile = async (profileId) => {
    if (!confirm('Are you sure you want to delete this guardrail profile?')) return;
    
    try {
      await api.delete(`/admin/providers/profiles/${profileId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchData();
    } catch (err) {
      console.error('Failed to delete profile:', err);
      setError('Failed to delete profile');
    }
  };

  const saveProfile = async (data) => {
    try {
      if (editingProfile) {
        await api.put(`/admin/providers/profiles/${editingProfile.id}`, data, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/admin/providers/profiles', data, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowProfileModal(false);
      setEditingProfile(null);
      fetchData();
    } catch (err) {
      console.error('Failed to save profile:', err);
      alert('Failed to save guardrail profile');
    }
  };

  const createExternalProvider = async (data) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadExternalProviders();
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

  const updateExternalProvider = async (id, data) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadExternalProviders();
        setShowProviderModal(false);
        setEditingProvider(null);
      }
    } catch (error) {
      console.error('Failed to update provider:', error);
    }
  };

  const deleteExternalProvider = async (id) => {
    if (!confirm('Are you sure you want to delete this provider?')) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadExternalProviders();
      }
    } catch (error) {
      console.error('Failed to delete provider:', error);
    }
  };

  const getStatusIcon = (enabled) => {
    return enabled ? (
      <CheckCircle className="text-green-500" size={20} />
    ) : (
      <XCircle className="text-gray-400" size={20} />
    );
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };
    return colors[severity] || colors.medium;
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-h-0">
        <Header title="Guardrails" />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-lime-600"></div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield },
    { id: 'profiles', label: 'Profiles', icon: Layers },
    { id: 'external', label: 'External Providers', icon: Globe },
    { id: 'templates', label: 'Templates', icon: Info },
    { id: 'test', label: 'Test', icon: Play },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Guardrails" />
      
      <div className="flex-1 overflow-auto p-4 md:p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-lime-100 rounded-lg">
                  <Shield className="w-6 h-6 text-lime-700" />
                </div>
                Guardrails
              </h1>
              <p className="text-gray-600 mt-1">Enterprise safety and compliance controls for AI requests</p>
            </div>
            <div className="flex gap-2">
              {activeTab === 'profiles' && (
                <button
                  onClick={() => {
                    setEditingProfile(null);
                    setShowProfileModal(true);
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
                >
                  <Plus size={18} />
                  <span>Create Profile</span>
                </button>
              )}
              {activeTab === 'external' && (
                <button
                  onClick={() => {
                    setEditingProvider(null);
                    setShowProviderModal(true);
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
                >
                  <Plus size={18} />
                  <span>Add Provider</span>
                </button>
              )}
              <button
                onClick={fetchData}
                className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 font-medium transition-colors"
              >
                <RefreshCw size={18} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-3">
              <AlertTriangle className="text-red-500" size={20} />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto pb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-lime-500 text-lime-700'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon size={18} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {activeTab === 'overview' && (
            <OverviewTab guardrails={guardrails} getStatusIcon={getStatusIcon} getSeverityColor={getSeverityColor} />
          )}

          {activeTab === 'profiles' && (
            <ProfilesTab 
              profiles={profiles} 
              canEdit={canEdit} 
              onEdit={(profile) => {
                setEditingProfile(profile);
                setShowProfileModal(true);
              }}
              onDelete={deleteProfile}
              onAdd={() => {
                setEditingProfile(null);
                setShowProfileModal(true);
              }}
            />
          )}

          {activeTab === 'external' && (
            <ExternalProvidersTab 
              providers={externalProviders}
              healthStatus={healthStatus}
              onEdit={(provider) => {
                setEditingProvider(provider);
                setShowProviderModal(true);
              }}
              onDelete={deleteExternalProvider}
              onTest={(provider) => {
                setTestingProvider(provider);
                setShowTestModal(true);
              }}
              onAdd={() => {
                setEditingProvider(null);
                setShowProviderModal(true);
              }}
            />
          )}

          {activeTab === 'templates' && enterpriseInfo && (
            <TemplatesTab enterpriseInfo={enterpriseInfo} />
          )}

          {activeTab === 'test' && (
            <TestTab 
              testInput={testInput}
              setTestInput={setTestInput}
              testResult={testResult}
              testing={testing}
              testGuardrails={testGuardrails}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsTab 
              policies={policies}
              selectedPolicy={selectedPolicy}
              setSelectedPolicy={setSelectedPolicy}
              saving={saving}
              updatePolicy={updatePolicy}
              canEdit={canEdit}
            />
          )}
        </div>
      </div>

      {showProfileModal && (
        <ProfileModal
          profile={editingProfile}
          onClose={() => {
            setShowProfileModal(false);
            setEditingProfile(null);
          }}
          onSave={saveProfile}
        />
      )}

      {showProviderModal && (
        <ProviderModal
          provider={editingProvider}
          onClose={() => {
            setShowProviderModal(false);
            setEditingProvider(null);
          }}
          onSave={(data) => {
            if (editingProvider) {
              updateExternalProvider(editingProvider.id, data);
            } else {
              createExternalProvider(data);
            }
          }}
        />
      )}

      {showTestModal && testingProvider && (
        <ExternalTestModal
          provider={testingProvider}
          token={token}
          onClose={() => {
            setShowTestModal(false);
            setTestingProvider(null);
          }}
        />
      )}
    </div>
  );
}

function OverviewTab({ guardrails, getStatusIcon, getSeverityColor }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Info size={20} className="text-lime-600" />
          How Guardrails Work
        </h2>
        <div className="space-y-4 text-sm text-gray-600">
          <p>
            Guardrails protect your AI Gateway by inspecting requests and responses for security threats, 
            compliance violations, and sensitive data. They run automatically on every API request.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className="bg-lime-50 rounded-xl p-4 border border-lime-100">
              <h3 className="font-medium text-gray-900 mb-2">Request Processing</h3>
              <ul className="space-y-1.5 text-sm">
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-lime-600" />
                  <span>PII detection and redaction</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-lime-600" />
                  <span>Prompt injection blocking</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-lime-600" />
                  <span>Jailbreak attempt detection</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-lime-600" />
                  <span>Content classification</span>
                </li>
              </ul>
            </div>
            <div className="bg-green-50 rounded-xl p-4 border border-green-100">
              <h3 className="font-medium text-gray-900 mb-2">Response Processing</h3>
              <ul className="space-y-1.5 text-sm">
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-green-600" />
                  <span>Output PII scanning</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-green-600" />
                  <span>Toxicity filtering</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-green-600" />
                  <span>Sensitive topic detection</span>
                </li>
                <li className="flex items-center gap-2">
                  <ChevronRight size={14} className="text-green-600" />
                  <span>Content sanitization</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {guardrails.map((guardrail, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-lime-100 rounded-lg">
                  <Shield className="text-lime-700" size={18} />
                </div>
                <h3 className="font-semibold">{guardrail.name}</h3>
              </div>
              {getStatusIcon(guardrail.enabled)}
            </div>
            <p className="text-sm text-gray-600 mb-3">{guardrail.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getSeverityColor(guardrail.severity)}`}>
                {guardrail.severity}
              </span>
              <span className="text-gray-500">{guardrail.category}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProfilesTab({ profiles, canEdit, onEdit, onDelete, onAdd }) {
  return (
    <div className="space-y-4">
      <div className="bg-lime-50 border border-lime-200 rounded-xl p-4 mb-6">
        <div className="flex items-start gap-3">
          <Layers className="text-lime-600 mt-0.5" size={20} />
          <div>
            <h3 className="font-medium text-gray-900">Guardrail Profiles</h3>
            <p className="text-sm text-gray-600 mt-1">
              Profiles define chains of request and response processors that run on API calls. 
              Assign profiles to tenants, API keys, or routes to apply specific guardrail rules.
            </p>
          </div>
        </div>
      </div>

      {profiles.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Guardrail Profiles</h3>
          <p className="text-gray-600 mb-6">
            Create guardrail profiles to define custom processor chains for your API requests.
          </p>
          <button
            onClick={onAdd}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
          >
            <Plus size={18} />
            Create Profile
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {profiles.map((profile) => (
            <div key={profile.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold">{profile.name}</h3>
                    {profile.is_enabled !== false && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                        Active
                      </span>
                    )}
                    {profile.tenant_id === null && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">
                        Global
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{profile.description || 'No description'}</p>
                </div>
                {canEdit && (
                  <div className="flex gap-2">
                    {profile.tenant_id !== null ? (
                      <button
                        onClick={() => onEdit(profile)}
                        className="p-2 text-gray-500 hover:text-lime-600 hover:bg-lime-50 rounded-lg transition-colors"
                        title="Edit profile"
                      >
                        <Edit2 size={16} />
                      </button>
                    ) : (
                      <span className="p-2 text-gray-300 cursor-not-allowed" title="Global profiles are read-only">
                        <Edit2 size={16} />
                      </span>
                    )}
                    {profile.tenant_id !== null ? (
                      <button
                        onClick={() => onDelete(profile.id)}
                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete profile"
                      >
                        <Trash2 size={16} />
                      </button>
                    ) : (
                      <span className="p-2 text-gray-300 cursor-not-allowed" title="Global profiles cannot be deleted">
                        <Trash2 size={16} />
                      </span>
                    )}
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Request Processors:</span>
                  <span className="ml-2 font-medium">{(profile.request_processors || []).length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Response Processors:</span>
                  <span className="ml-2 font-medium">{(profile.response_processors || []).length}</span>
                </div>
              </div>

              {((profile.request_processors || []).length > 0 || (profile.response_processors || []).length > 0) && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex flex-wrap gap-1">
                    {(profile.request_processors || []).slice(0, 3).map((p, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-lime-50 text-lime-700 text-xs rounded font-medium">
                        {p.name || p.type}
                      </span>
                    ))}
                    {(profile.response_processors || []).slice(0, 3).map((p, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded font-medium">
                        {p.name || p.type}
                      </span>
                    ))}
                    {((profile.request_processors || []).length + (profile.response_processors || []).length) > 6 && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded font-medium">
                        +{(profile.request_processors || []).length + (profile.response_processors || []).length - 6} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ExternalProvidersTab({ providers, healthStatus, onEdit, onDelete, onTest, onAdd }) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-lg font-semibold">Configured Providers</h2>
            <p className="text-sm text-gray-600 mt-1">Integrate 3rd party guardrail services for enhanced content safety</p>
          </div>
        </div>

        {providers.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Globe className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-lg font-medium text-gray-700 mb-2">No external providers configured</p>
            <p className="text-gray-500 mb-6">Add external guardrail services to enhance your content safety.</p>
            <button
              onClick={onAdd}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
            >
              <Plus size={18} />
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
                onEdit={() => onEdit(provider)}
                onDelete={() => onDelete(provider.id)}
                onTest={() => onTest(provider)}
              />
            ))}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Available Provider Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {PROVIDER_TYPES.map((type) => (
            <div key={type.value} className="border border-gray-200 rounded-xl p-4 hover:bg-gray-50 transition-colors">
              <h3 className="font-semibold text-gray-900 mb-1">{type.label}</h3>
              <p className="text-sm text-gray-600">{type.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ProviderCard({ provider, healthStatus, onEdit, onDelete, onTest }) {
  const providerType = PROVIDER_TYPES.find(t => t.value === provider.provider_type);
  
  return (
    <div className="border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow bg-white">
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
            className="p-2 text-gray-600 hover:text-lime-600 hover:bg-lime-50 rounded-lg transition-colors"
            title="Test provider"
          >
            <TestTube className="w-4 h-4" />
          </button>
          <button
            onClick={onEdit}
            className="p-2 text-gray-600 hover:text-lime-600 hover:bg-lime-50 rounded-lg transition-colors"
            title="Edit provider"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
        <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
          provider.is_enabled
            ? 'bg-green-100 text-green-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {provider.is_enabled ? 'Enabled' : 'Disabled'}
        </span>
        {provider.is_global && (
          <span className="px-2 py-1 rounded-lg text-xs font-medium bg-lime-100 text-lime-800">
            Global
          </span>
        )}
      </div>

      {provider.capabilities && provider.capabilities.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Capabilities</p>
          <div className="flex flex-wrap gap-1">
            {provider.capabilities.slice(0, 3).map((cap) => (
              <span key={cap} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                {cap}
              </span>
            ))}
            {provider.capabilities.length > 3 && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                +{provider.capabilities.length - 3}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TemplatesTab({ enterpriseInfo }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-lime-100 rounded-lg">
            <Shield size={28} className="text-lime-700" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Enterprise Compliance Templates</h2>
            <p className="text-gray-600">Pre-built guardrail configurations for common compliance requirements</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <div className="bg-lime-50 border border-lime-200 rounded-xl p-4">
            <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.total_rules || 0}</p>
            <p className="text-sm text-gray-600">Total Rules</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.enabled_count || 0}</p>
            <p className="text-sm text-gray-600">Active</p>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
            <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.pii_patterns || 0}</p>
            <p className="text-sm text-gray-600">PII Patterns</p>
          </div>
          <div className="bg-teal-50 border border-teal-200 rounded-xl p-4">
            <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.compliance_frameworks?.length || 0}</p>
            <p className="text-sm text-gray-600">Frameworks</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Info className="text-lime-600" size={20} />
            PII Detection Patterns
          </h3>
          <div className="space-y-2">
            {(enterpriseInfo.pii_types || ['SSN', 'Credit Card', 'Bank Account', 'Aadhaar', 'PAN', 'Email', 'Phone']).map((type, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <CheckCircle className="text-green-500" size={16} />
                <span>{type}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="text-orange-600" size={20} />
            Sensitive Content Guard
          </h3>
          <p className="text-sm text-gray-600 mb-3">
            Detects and flags sensitive content including investment advice, medical recommendations, and legal opinions.
          </p>
          <div className="space-y-2">
            {['Financial advice', 'Medical recommendations', 'Legal opinions', 'Personal data requests'].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <Shield className="text-orange-500" size={16} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Shield className="text-red-600" size={20} />
            Security Controls
          </h3>
          <div className="space-y-2">
            {['Prompt injection detection', 'Jailbreak prevention', 'Confidential data protection', 'Output sanitization'].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <CheckCircle className="text-green-500" size={16} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Info className="text-lime-600" size={20} />
            Compliance Frameworks
          </h3>
          <div className="flex flex-wrap gap-2">
            {(enterpriseInfo.compliance_frameworks || ['PCI-DSS', 'SOC 2', 'GDPR', 'HIPAA', 'SOX']).map((framework, idx) => (
              <span key={idx} className="px-3 py-1.5 bg-lime-100 text-lime-800 rounded-full text-sm font-medium">
                {framework}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TestTab({ testInput, setTestInput, testResult, testing, testGuardrails }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="font-semibold mb-4 flex items-center gap-2">
        <Play className="text-lime-600" size={20} />
        Test Guardrails
      </h3>
      <p className="text-gray-600 mb-4">
        Enter text to test against all active guardrails. This will check for PII, toxicity, prompt injection, and other violations.
      </p>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Test Input</label>
          <textarea
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            rows={4}
            placeholder="Enter text to test..."
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
          />
        </div>

        <button
          onClick={testGuardrails}
          disabled={testing || !testInput.trim()}
          className="flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {testing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Testing...
            </>
          ) : (
            <>
              <Play size={18} />
              Run Test
            </>
          )}
        </button>

        {testResult && (
          <div className="mt-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              {testResult.blocked ? (
                <>
                  <XCircle className="text-red-500" size={20} />
                  <span className="text-red-700">Content Blocked</span>
                </>
              ) : (
                <>
                  <CheckCircle className="text-green-500" size={20} />
                  <span className="text-green-700">Content Passed</span>
                </>
              )}
            </h4>

            {testResult.violations && testResult.violations.length > 0 && (
              <div className="space-y-2 mt-3">
                <p className="text-sm font-medium text-gray-700">Violations Found:</p>
                {testResult.violations.map((v, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm bg-red-50 text-red-700 px-3 py-2 rounded-lg">
                    <AlertTriangle size={16} />
                    <span>{v.type}: {v.message}</span>
                  </div>
                ))}
              </div>
            )}

            {testResult.redacted_text && (
              <div className="mt-3">
                <p className="text-sm font-medium text-gray-700">Redacted Output:</p>
                <pre className="mt-2 p-3 bg-white border border-gray-200 rounded-lg text-sm overflow-x-auto">
                  {testResult.redacted_text}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsTab({ policies, selectedPolicy, setSelectedPolicy, saving, updatePolicy, canEdit }) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Settings className="text-lime-600" size={20} />
          Global Guardrail Policy
        </h3>
        <p className="text-gray-600 mb-4">
          Select the default guardrail policy to apply across all API requests when no specific profile is assigned.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {policies.map((policy) => (
            <div
              key={policy.id}
              onClick={() => canEdit && setSelectedPolicy(policy.id)}
              className={`p-4 border rounded-xl cursor-pointer transition-all ${
                selectedPolicy === policy.id
                  ? 'border-lime-500 bg-lime-50 ring-2 ring-lime-200'
                  : 'border-gray-200 hover:border-lime-300 hover:bg-gray-50'
              } ${!canEdit && 'cursor-not-allowed opacity-75'}`}
            >
              <h4 className="font-medium text-gray-900">{policy.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{policy.description}</p>
            </div>
          ))}
        </div>

        {canEdit && (
          <button
            onClick={updatePolicy}
            disabled={saving}
            className="mt-4 flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 disabled:opacity-50 font-medium transition-colors"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <Save size={18} />
                Save Policy
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

function ProfileModal({ profile, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    description: profile?.description || '',
    is_enabled: profile?.is_enabled !== false,
    request_processors: profile?.request_processors || [],
    response_processors: profile?.response_processors || [],
  });
  const [saving, setSaving] = useState(false);

  const processorTypes = [
    { value: 'pii_detection', label: 'PII Detection', description: 'Detect and redact personal information' },
    { value: 'toxicity_filter', label: 'Toxicity Filter', description: 'Block toxic or harmful content' },
    { value: 'prompt_injection', label: 'Prompt Injection Detection', description: 'Detect malicious prompt injections' },
    { value: 'jailbreak_detection', label: 'Jailbreak Detection', description: 'Prevent model jailbreaks' },
    { value: 'content_classification', label: 'Content Classification', description: 'Classify content by category' },
    { value: 'rate_limiting', label: 'Rate Limiting', description: 'Apply request rate limits' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  const addProcessor = (stage) => {
    const newProcessor = { type: 'pii_detection', name: 'New Processor', config: {} };
    if (stage === 'request') {
      setFormData({ ...formData, request_processors: [...formData.request_processors, newProcessor] });
    } else {
      setFormData({ ...formData, response_processors: [...formData.response_processors, newProcessor] });
    }
  };

  const removeProcessor = (stage, index) => {
    if (stage === 'request') {
      setFormData({ 
        ...formData, 
        request_processors: formData.request_processors.filter((_, i) => i !== index) 
      });
    } else {
      setFormData({ 
        ...formData, 
        response_processors: formData.response_processors.filter((_, i) => i !== index) 
      });
    }
  };

  const updateProcessor = (stage, index, field, value) => {
    if (stage === 'request') {
      const updated = [...formData.request_processors];
      updated[index] = { ...updated[index], [field]: value };
      setFormData({ ...formData, request_processors: updated });
    } else {
      const updated = [...formData.response_processors];
      updated[index] = { ...updated[index], [field]: value };
      setFormData({ ...formData, response_processors: updated });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {profile ? 'Edit Profile' : 'Create Guardrail Profile'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                rows="2"
              />
            </div>

            <div className="flex items-center gap-2.5">
              <input
                type="checkbox"
                id="is_enabled"
                checked={formData.is_enabled}
                onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                className="rounded border-gray-300 text-lime-600 focus:ring-lime-500"
              />
              <label htmlFor="is_enabled" className="text-sm font-medium text-gray-700">Enable this profile</label>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Request Processors</label>
                <button
                  type="button"
                  onClick={() => addProcessor('request')}
                  className="text-sm text-lime-600 hover:text-lime-700 font-medium flex items-center gap-1"
                >
                  <Plus size={16} /> Add
                </button>
              </div>
              <div className="space-y-2">
                {formData.request_processors.map((processor, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3 bg-lime-50 rounded-xl border border-lime-100">
                    <select
                      value={processor.type}
                      onChange={(e) => updateProcessor('request', idx, 'type', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-lime-500"
                    >
                      {processorTypes.map(pt => (
                        <option key={pt.value} value={pt.value}>{pt.label}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeProcessor('request', idx)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
                {formData.request_processors.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-3 bg-gray-50 rounded-xl">No request processors</p>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Response Processors</label>
                <button
                  type="button"
                  onClick={() => addProcessor('response')}
                  className="text-sm text-lime-600 hover:text-lime-700 font-medium flex items-center gap-1"
                >
                  <Plus size={16} /> Add
                </button>
              </div>
              <div className="space-y-2">
                {formData.response_processors.map((processor, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-100">
                    <select
                      value={processor.type}
                      onChange={(e) => updateProcessor('response', idx, 'type', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-lime-500"
                    >
                      {processorTypes.map(pt => (
                        <option key={pt.value} value={pt.value}>{pt.label}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeProcessor('response', idx)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
                {formData.response_processors.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-3 bg-gray-50 rounded-xl">No response processors</p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium disabled:opacity-50 transition-colors"
                disabled={saving}
              >
                {saving ? 'Saving...' : profile ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
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
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const data = { ...formData };
    data.timeout_seconds = parseInt(data.timeout_seconds);
    data.retry_attempts = parseInt(data.retry_attempts);
    data.priority = parseInt(data.priority);
    
    Object.keys(data.thresholds).forEach(key => {
      data.thresholds[key] = parseFloat(data.thresholds[key]);
    });
    
    if (!data.api_key) {
      delete data.api_key;
    }
    
    await onSave(data);
    setSaving(false);
  };

  const selectedType = PROVIDER_TYPES.find(t => t.value === formData.provider_type);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {provider ? 'Edit Provider' : 'Add Guardrail Provider'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Provider Type *</label>
              <select
                required
                value={formData.provider_type}
                onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                disabled={!!provider}
              >
                {PROVIDER_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
              {selectedType && <p className="mt-1.5 text-sm text-gray-500">{selectedType.description}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                placeholder="e.g., Production OpenAI Moderation"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">API Key {!provider && '*'}</label>
              <input
                type="password"
                required={!provider}
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                placeholder={provider ? "Leave empty to keep existing key" : "Enter API key"}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">API Endpoint</label>
                <input
                  type="url"
                  value={formData.api_endpoint}
                  onChange={(e) => setFormData({ ...formData, api_endpoint: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                  placeholder="Optional custom endpoint"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Region</label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                  placeholder="e.g., us-east-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Timeout (sec)</label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Retries</label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={formData.retry_attempts}
                  onChange={(e) => setFormData({ ...formData, retry_attempts: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Priority</label>
                <input
                  type="number"
                  min="0"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <input
                type="checkbox"
                id="is_global"
                checked={formData.is_global}
                onChange={(e) => setFormData({ ...formData, is_global: e.target.checked })}
                className="rounded border-gray-300 text-lime-600 focus:ring-lime-500"
              />
              <label htmlFor="is_global" className="text-sm font-medium text-gray-700">
                Global provider (available to all tenants)
              </label>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium disabled:opacity-50 transition-colors"
                disabled={saving}
              >
                {saving ? 'Saving...' : provider ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function ExternalTestModal({ provider, token, onClose }) {
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/guardrails/external/providers/${provider.id}/test`, {
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
        setResult({ error: error.detail || 'Test failed' });
      }
    } catch (error) {
      console.error('Test failed:', error);
      setResult({ error: 'Test failed: ' + error.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Test {provider.name}</h2>
          <p className="text-gray-600 mb-6">Test this external guardrail provider with sample content</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Stage</label>
              <select
                value={testStage}
                onChange={(e) => setTestStage(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              >
                <option value="input">Input (Request)</option>
                <option value="output">Output (Response)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Test Content</label>
              <textarea
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                rows={4}
                placeholder="Enter text to test..."
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              />
            </div>

            <button
              onClick={runTest}
              disabled={testing || !testText.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 disabled:opacity-50 font-medium transition-colors"
            >
              {testing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Testing...
                </>
              ) : (
                <>
                  <TestTube size={18} />
                  Run Test
                </>
              )}
            </button>

            {result && (
              <div className={`p-4 rounded-xl ${result.error ? 'bg-red-50 border border-red-200' : 'bg-gray-50 border border-gray-200'}`}>
                {result.error ? (
                  <p className="text-red-700">{result.error}</p>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      {result.flagged ? (
                        <>
                          <XCircle className="text-red-500" size={20} />
                          <span className="font-medium text-red-700">Content Flagged</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="text-green-500" size={20} />
                          <span className="font-medium text-green-700">Content Passed</span>
                        </>
                      )}
                    </div>
                    {result.scores && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-700 mb-2">Scores:</p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          {Object.entries(result.scores).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                              <span className="font-medium">{(value * 100).toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
