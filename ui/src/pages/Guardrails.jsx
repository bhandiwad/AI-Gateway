import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
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
  X
} from 'lucide-react';

export default function Guardrails() {
  const { token, hasPermission } = useAuth();
  const [guardrails, setGuardrails] = useState([]);
  const [bfsiGuardrails, setBfsiGuardrails] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [customPolicies, setCustomPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('strict');
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [policyForm, setPolicyForm] = useState({
    name: '',
    description: '',
    config: {
      pii_detection: { enabled: true, action: 'redact' },
      toxicity_filter: { enabled: true, threshold: 0.7, action: 'block' },
      prompt_injection: { enabled: true, action: 'block' },
      jailbreak_detection: { enabled: true, action: 'block' },
      financial_advice: { enabled: false, action: 'warn' },
      max_tokens: { enabled: true, limit: 4096 }
    }
  });

  const canEdit = hasPermission('guardrails:edit');

  useEffect(() => {
    fetchGuardrails();
  }, [token]);

  const fetchGuardrails = async () => {
    try {
      setLoading(true);
      setError(null);

      const [guardrailsRes, bfsiRes, policiesRes, customRes] = await Promise.all([
        api.get('/admin/guardrails', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/guardrails/bfsi', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/guardrails/policies', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/admin/guardrails/custom', {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: { policies: [] } }))
      ]);

      setGuardrails(guardrailsRes.data.guardrails || []);
      setBfsiGuardrails(bfsiRes.data);
      setPolicies(policiesRes.data.policies || []);
      setCustomPolicies(customRes.data.policies || []);
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

  const openCreateModal = () => {
    setEditingPolicy(null);
    setPolicyForm({
      name: '',
      description: '',
      config: {
        pii_detection: { enabled: true, action: 'redact' },
        toxicity_filter: { enabled: true, threshold: 0.7, action: 'block' },
        prompt_injection: { enabled: true, action: 'block' },
        jailbreak_detection: { enabled: true, action: 'block' },
        financial_advice: { enabled: false, action: 'warn' },
        max_tokens: { enabled: true, limit: 4096 }
      }
    });
    setShowPolicyModal(true);
  };

  const openEditModal = (policy) => {
    setEditingPolicy(policy);
    setPolicyForm({
      name: policy.name,
      description: policy.description || '',
      config: policy.config || {}
    });
    setShowPolicyModal(true);
  };

  const saveCustomPolicy = async () => {
    try {
      setSaving(true);
      if (editingPolicy) {
        await api.put(`/admin/guardrails/custom/${editingPolicy.id}`, policyForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.post('/admin/guardrails/custom', policyForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowPolicyModal(false);
      fetchGuardrails();
    } catch (err) {
      console.error('Failed to save policy:', err);
      setError('Failed to save policy');
    } finally {
      setSaving(false);
    }
  };

  const deleteCustomPolicy = async (policyId) => {
    if (!confirm('Are you sure you want to delete this policy?')) return;
    
    try {
      await api.delete(`/admin/guardrails/custom/${policyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchGuardrails();
    } catch (err) {
      console.error('Failed to delete policy:', err);
      setError('Failed to delete policy');
    }
  };

  const activateCustomPolicy = async (policyId) => {
    try {
      await api.post(`/admin/guardrails/custom/${policyId}/activate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchGuardrails();
    } catch (err) {
      console.error('Failed to activate policy:', err);
      setError('Failed to activate policy');
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Guardrails</h1>
            <p className="text-gray-600 mt-1">Enterprise safety and compliance controls</p>
          </div>
          <div className="flex gap-2">
            {canEdit && (
              <button
                onClick={openCreateModal}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 min-h-[44px]"
              >
                <Plus size={18} />
                <span>New Policy</span>
              </button>
            )}
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
          {['overview', 'custom', 'bfsi', 'test', 'settings'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap min-h-[44px] ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              {tab === 'custom' ? 'Custom Policies' : tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {guardrails.map((guardrail, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Shield className="text-blue-600" size={20} />
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
        )}

        {activeTab === 'custom' && (
          <div className="space-y-4">
            {customPolicies.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <Shield className="mx-auto text-gray-400 mb-4" size={48} />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Custom Policies</h3>
                <p className="text-gray-500 mb-4">
                  Create custom guardrail policies tailored to your organization's needs.
                </p>
                {canEdit && (
                  <button
                    onClick={openCreateModal}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus size={18} />
                    Create Policy
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {customPolicies.map((policy) => (
                  <div key={policy.id} className="bg-white rounded-lg shadow p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{policy.name}</h3>
                          {policy.is_default && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                              Active
                            </span>
                          )}
                          {!policy.is_active && (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs rounded-full">
                              Disabled
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{policy.description}</p>
                      </div>
                      {canEdit && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEditModal(policy)}
                            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            onClick={() => deleteCustomPolicy(policy.id)}
                            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                      {Object.entries(policy.config || {}).slice(0, 4).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-1">
                          {value?.enabled ? (
                            <CheckCircle className="text-green-500" size={12} />
                          ) : (
                            <XCircle className="text-gray-400" size={12} />
                          )}
                          <span className="text-gray-600">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                        </div>
                      ))}
                    </div>
                    
                    {canEdit && !policy.is_default && (
                      <button
                        onClick={() => activateCustomPolicy(policy.id)}
                        className="w-full mt-2 px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100"
                      >
                        Set as Active
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'bfsi' && bfsiGuardrails && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <Shield size={32} className="text-gray-700" />
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Compliance Suite</h2>
                  <p className="text-gray-600">Industry compliance guardrails</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{bfsiGuardrails.total_rules || 0}</p>
                  <p className="text-sm text-gray-500">Total Rules</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{bfsiGuardrails.enabled_count || 0}</p>
                  <p className="text-sm text-gray-500">Active</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{bfsiGuardrails.pii_patterns || 0}</p>
                  <p className="text-sm text-gray-500">PII Patterns</p>
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-2xl font-bold text-gray-900">{bfsiGuardrails.compliance_frameworks?.length || 0}</p>
                  <p className="text-sm text-gray-500">Frameworks</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Info className="text-blue-600" size={20} />
                  PII Detection
                </h3>
                <div className="space-y-2">
                  {(bfsiGuardrails.pii_types || ['SSN', 'Credit Card', 'Bank Account', 'Aadhaar', 'PAN']).map((type, idx) => (
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
                  Financial Advice Guard
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Detects and flags investment recommendations, financial advice, and market predictions.
                </p>
                <div className="space-y-2">
                  {['Investment recommendations', 'Stock tips', 'Market predictions', 'Trading advice'].map((item, idx) => (
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
                  {(bfsiGuardrails.compliance_frameworks || ['PCI-DSS', 'SOX', 'GDPR', 'RBI Guidelines']).map((framework, idx) => (
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
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[120px]"
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
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Settings className="text-gray-600" size={20} />
                Policy Configuration
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Policy Template</label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {policies.length > 0 ? policies.map((policy) => (
                      <button
                        key={policy.id}
                        onClick={() => setSelectedPolicy(policy.id)}
                        disabled={!canEdit}
                        className={`p-4 rounded-lg border-2 text-left transition-colors ${
                          selectedPolicy === policy.id
                            ? 'border-blue-600 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        } ${!canEdit ? 'cursor-not-allowed opacity-75' : ''}`}
                      >
                        <h4 className="font-medium">{policy.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{policy.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {policy.features?.slice(0, 3).map((feature, idx) => (
                            <span key={idx} className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                              {feature}
                            </span>
                          ))}
                        </div>
                      </button>
                    )) : (
                      <>
                        {['strict', 'balanced', 'permissive'].map((p) => (
                          <button
                            key={p}
                            onClick={() => setSelectedPolicy(p)}
                            disabled={!canEdit}
                            className={`p-4 rounded-lg border-2 text-left ${
                              selectedPolicy === p ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                            } ${!canEdit ? 'cursor-not-allowed opacity-75' : ''}`}
                          >
                            <h4 className="font-medium capitalize">{p}</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              {p === 'strict' && 'Maximum protection for regulated environments'}
                              {p === 'balanced' && 'Balance between safety and usability'}
                              {p === 'permissive' && 'Minimal restrictions for internal use'}
                            </p>
                          </button>
                        ))}
                      </>
                    )}
                  </div>
                </div>

                {canEdit && (
                  <button
                    onClick={updatePolicy}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
                  >
                    <Save size={18} />
                    <span>{saving ? 'Saving...' : 'Save Policy'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {showPolicyModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between p-4 border-b">
                <h3 className="text-lg font-semibold">
                  {editingPolicy ? 'Edit Policy' : 'Create Custom Policy'}
                </h3>
                <button
                  onClick={() => setShowPolicyModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-full"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="p-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Policy Name</label>
                  <input
                    type="text"
                    value={policyForm.name}
                    onChange={(e) => setPolicyForm({...policyForm, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Strict Compliance Policy"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={policyForm.description}
                    onChange={(e) => setPolicyForm({...policyForm, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    rows={2}
                    placeholder="Describe this policy..."
                  />
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">Guardrail Settings</h4>
                  <div className="space-y-3">
                    {[
                      { key: 'pii_detection', label: 'PII Detection', desc: 'Detect and redact personally identifiable information' },
                      { key: 'toxicity_filter', label: 'Toxicity Filter', desc: 'Block toxic or harmful content' },
                      { key: 'prompt_injection', label: 'Prompt Injection Detection', desc: 'Block manipulation attempts' },
                      { key: 'jailbreak_detection', label: 'Jailbreak Detection', desc: 'Prevent AI safety bypass' },
                      { key: 'financial_advice', label: 'Financial Advice Guard', desc: 'Flag investment recommendations' },
                    ].map((item) => (
                      <div key={item.key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-sm">{item.label}</p>
                          <p className="text-xs text-gray-500">{item.desc}</p>
                        </div>
                        <button
                          onClick={() => {
                            const newConfig = {...policyForm.config};
                            if (!newConfig[item.key]) newConfig[item.key] = { enabled: false };
                            newConfig[item.key].enabled = !newConfig[item.key]?.enabled;
                            setPolicyForm({...policyForm, config: newConfig});
                          }}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            policyForm.config[item.key]?.enabled ? 'bg-green-600' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              policyForm.config[item.key]?.enabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end gap-3 p-4 border-t">
                <button
                  onClick={() => setShowPolicyModal(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveCustomPolicy}
                  disabled={saving || !policyForm.name.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : (editingPolicy ? 'Update Policy' : 'Create Policy')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
