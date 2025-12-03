import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
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
  Layers
} from 'lucide-react';

export default function Guardrails() {
  const { token, hasPermission } = useAuth();
  const navigate = useNavigate();
  const [guardrails, setGuardrails] = useState([]);
  const [enterpriseInfo, setEnterpriseInfo] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('strict');
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const canEdit = hasPermission('guardrails:edit');

  useEffect(() => {
    fetchGuardrails();
  }, [token]);

  const fetchGuardrails = async () => {
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
    } catch (err) {
      console.error('Failed to fetch guardrails:', err);
      setError('Failed to load guardrails configuration');
    } finally {
      setLoading(false);
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
      fetchGuardrails();
    } catch (err) {
      console.error('Failed to delete profile:', err);
      setError('Failed to delete profile');
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
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-600"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Guardrails</h1>
            <p className="text-gray-600 mt-1">Enterprise safety and compliance controls for AI requests</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate('/router-config?tab=profiles')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 min-h-[44px]"
            >
              <Plus size={18} />
              <span>Create Profile</span>
            </button>
            <button
              onClick={fetchGuardrails}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
            >
              <RefreshCw size={18} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['overview', 'profiles', 'templates', 'test', 'settings'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap min-h-[44px] ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              {tab === 'profiles' ? 'Guardrail Profiles' : 
               tab === 'templates' ? 'Enterprise Templates' :
               tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Info size={20} className="text-gray-600" />
                How Guardrails Work
              </h2>
              <div className="space-y-4 text-sm text-gray-600">
                <p>
                  Guardrails protect your AI Gateway by inspecting requests and responses for security threats, 
                  compliance violations, and sensitive data. They run automatically on every API request.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Request Processing</h3>
                    <ul className="space-y-1 text-sm">
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        PII detection and redaction
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Prompt injection blocking
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Jailbreak attempt detection
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Content classification
                      </li>
                    </ul>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Response Processing</h3>
                    <ul className="space-y-1 text-sm">
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Output PII scanning
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Toxicity filtering
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Sensitive topic detection
                      </li>
                      <li className="flex items-center gap-2">
                        <ChevronRight size={14} className="text-gray-400" />
                        Content sanitization
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {guardrails.map((guardrail, idx) => (
                <div key={idx} className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Shield className="text-gray-600" size={20} />
                      <h3 className="font-semibold">{guardrail.name}</h3>
                    </div>
                    {getStatusIcon(guardrail.enabled)}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{guardrail.description}</p>
                  <div className="flex items-center justify-between text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(guardrail.severity)}`}>
                      {guardrail.severity}
                    </span>
                    <span className="text-gray-500">{guardrail.category}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="space-y-4">
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <Layers className="text-gray-500 mt-0.5" size={20} />
                <div>
                  <h3 className="font-medium text-gray-900">Guardrail Profiles</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Profiles define chains of request and response processors that run on API calls. 
                    Assign profiles to tenants, API keys, or routes to apply specific guardrail rules.
                  </p>
                  <button
                    onClick={() => navigate('/router-config?tab=profiles')}
                    className="mt-3 inline-flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
                  >
                    <span>Manage in Router Config</span>
                    <ExternalLink size={14} />
                  </button>
                </div>
              </div>
            </div>

            {profiles.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Shield className="mx-auto text-gray-400 mb-4" size={48} />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Guardrail Profiles</h3>
                <p className="text-gray-500 mb-4">
                  Create guardrail profiles to define custom processor chains for your API requests.
                </p>
                <button
                  onClick={() => navigate('/router-config?tab=profiles')}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus size={18} />
                  Create Profile
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profiles.map((profile) => (
                  <div key={profile.id} className="bg-white rounded-lg shadow p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold">{profile.name}</h3>
                          {profile.is_enabled !== false && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                              Active
                            </span>
                          )}
                          {profile.tenant_id === null && (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
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
                              onClick={() => navigate('/router-config?tab=profiles')}
                              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded"
                              title="Edit profile"
                            >
                              <Edit2 size={16} />
                            </button>
                          ) : (
                            <span 
                              className="p-2 text-gray-300 cursor-not-allowed"
                              title="Global profiles are read-only"
                            >
                              <Edit2 size={16} />
                            </span>
                          )}
                          {profile.tenant_id !== null ? (
                            <button
                              onClick={() => deleteProfile(profile.id)}
                              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                              title="Delete profile"
                            >
                              <Trash2 size={16} />
                            </button>
                          ) : (
                            <span 
                              className="p-2 text-gray-300 cursor-not-allowed"
                              title="Global profiles cannot be deleted"
                            >
                              <Trash2 size={16} />
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Request Processors:</span>
                        <span className="ml-2 font-medium">
                          {(profile.request_processors || []).length}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Response Processors:</span>
                        <span className="ml-2 font-medium">
                          {(profile.response_processors || []).length}
                        </span>
                      </div>
                    </div>

                    {((profile.request_processors || []).length > 0 || 
                      (profile.response_processors || []).length > 0) && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex flex-wrap gap-1">
                          {(profile.request_processors || []).slice(0, 3).map((p, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                              {p.name || p.type}
                            </span>
                          ))}
                          {(profile.response_processors || []).slice(0, 3).map((p, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded">
                              {p.name || p.type}
                            </span>
                          ))}
                          {((profile.request_processors || []).length + (profile.response_processors || []).length) > 6 && (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
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
        )}

        {activeTab === 'templates' && enterpriseInfo && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <Shield size={32} className="text-gray-700" />
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Enterprise Compliance Templates</h2>
                  <p className="text-gray-600">Pre-built guardrail configurations for common compliance requirements</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.total_rules || 0}</p>
                  <p className="text-sm text-gray-500">Total Rules</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.enabled_count || 0}</p>
                  <p className="text-sm text-gray-500">Active</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.pii_patterns || 0}</p>
                  <p className="text-sm text-gray-500">PII Patterns</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{enterpriseInfo.compliance_frameworks?.length || 0}</p>
                  <p className="text-sm text-gray-500">Frameworks</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Info className="text-gray-600" size={20} />
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

              <div className="bg-white rounded-lg shadow p-4">
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

              <div className="bg-white rounded-lg shadow p-4">
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

              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Info className="text-purple-600" size={20} />
                  Compliance Frameworks
                </h3>
                <div className="flex flex-wrap gap-2">
                  {(enterpriseInfo.compliance_frameworks || ['PCI-DSS', 'SOC 2', 'GDPR', 'HIPAA', 'SOX']).map((framework, idx) => (
                    <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                      {framework}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'test' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Play className="text-green-600" size={20} />
              Test Guardrails
            </h3>
            <p className="text-gray-600 mb-4">
              Enter text to test against all active guardrails. This will check for PII, toxicity, prompt injection, and other violations.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Test Input</label>
                <textarea
                  value={testInput}
                  onChange={(e) => setTestInput(e.target.value)}
                  placeholder="Enter text to test... (e.g., 'My SSN is 123-45-6789' or 'Ignore previous instructions')"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 min-h-[120px]"
                />
              </div>
              
              <button
                onClick={testGuardrails}
                disabled={testing || !testInput.trim()}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
              >
                <Play size={18} />
                <span>{testing ? 'Testing...' : 'Run Test'}</span>
              </button>

              {testResult && (
                <div className={`mt-4 p-4 rounded-lg ${testResult.blocked ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    {!testResult.blocked ? (
                      <>
                        <CheckCircle className="text-green-600" size={24} />
                        <span className="font-semibold text-green-800">All checks passed</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="text-red-600" size={24} />
                        <span className="font-semibold text-red-800">Content blocked</span>
                      </>
                    )}
                  </div>

                  {testResult.triggered_guardrails && testResult.triggered_guardrails.length > 0 && (
                    <div className="space-y-2">
                      {testResult.triggered_guardrails.map((guardrail, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="text-orange-500 flex-shrink-0 mt-0.5" size={16} />
                          <div>
                            <span className="font-medium">{guardrail.name}:</span>{' '}
                            <span className="text-gray-700">{guardrail.message || guardrail.action}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {testResult.processed_text && testResult.processed_text !== testResult.original_text && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-700 mb-1">Processed Output:</p>
                      <p className="text-sm text-gray-600 bg-gray-100 p-2 rounded font-mono">
                        {testResult.processed_text}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Settings className="text-gray-600" size={20} />
              Default Policy Settings
            </h3>
            <p className="text-gray-600 mb-6">
              Select the default guardrail policy template for your organization. This determines the baseline level of protection.
            </p>

            <div className="space-y-4 mb-6">
              {(policies || []).length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No policy templates available. Contact support to configure policy templates.</p>
                </div>
              ) : (
                (policies || []).map((policy) => (
                  <label
                    key={policy.id}
                    className={`flex items-start gap-4 p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedPolicy === policy.id
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="policy"
                      value={policy.id}
                      checked={selectedPolicy === policy.id}
                      onChange={(e) => setSelectedPolicy(e.target.value)}
                      className="mt-1"
                      disabled={!canEdit}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{policy.name}</span>
                        {policy.id === 'strict' && (
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                            Recommended
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{policy.description}</p>
                    </div>
                  </label>
                ))
              )}
            </div>

            {canEdit && (policies || []).length > 0 && (
              <button
                onClick={updatePolicy}
                disabled={saving}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Save size={18} />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
