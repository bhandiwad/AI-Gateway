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
  Save
} from 'lucide-react';

export default function Guardrails() {
  const { token } = useAuth();
  const [guardrails, setGuardrails] = useState([]);
  const [bfsiGuardrails, setBfsiGuardrails] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState('strict');
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchGuardrails();
  }, [token]);

  const fetchGuardrails = async () => {
    try {
      setLoading(true);
      setError(null);

      const [guardrailsRes, bfsiRes, policiesRes] = await Promise.all([
        api.get('/api/v1/admin/guardrails', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/v1/admin/guardrails/bfsi', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/v1/admin/guardrails/policies', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setGuardrails(guardrailsRes.data.guardrails || []);
      setBfsiGuardrails(bfsiRes.data);
      setPolicies(policiesRes.data.policies || []);
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

      const response = await api.post('/api/v1/admin/guardrails/test', {
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
      await api.put('/api/v1/admin/guardrails/policy', {
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
            <p className="text-gray-600 mt-1">BFSI-compliant safety and compliance controls</p>
          </div>
          <button
            onClick={fetchGuardrails}
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
          {['overview', 'bfsi', 'test', 'settings'].map((tab) => (
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

        {activeTab === 'bfsi' && bfsiGuardrails && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
              <div className="flex items-center gap-3 mb-4">
                <Shield size={32} />
                <div>
                  <h2 className="text-xl font-bold">BFSI Compliance Suite</h2>
                  <p className="text-blue-100">Banking, Financial Services & Insurance guardrails</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{bfsiGuardrails.total_rules || 0}</p>
                  <p className="text-sm text-blue-100">Total Rules</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{bfsiGuardrails.enabled_count || 0}</p>
                  <p className="text-sm text-blue-100">Active</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{bfsiGuardrails.pii_patterns || 0}</p>
                  <p className="text-sm text-blue-100">PII Patterns</p>
                </div>
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-2xl font-bold">{bfsiGuardrails.compliance_frameworks?.length || 0}</p>
                  <p className="text-sm text-blue-100">Frameworks</p>
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
                <div className={`mt-4 p-4 rounded-lg ${testResult.passed ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    {testResult.passed ? (
                      <>
                        <CheckCircle className="text-green-600" size={24} />
                        <span className="font-semibold text-green-800">All checks passed</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="text-red-600" size={24} />
                        <span className="font-semibold text-red-800">Violations detected</span>
                      </>
                    )}
                  </div>

                  {testResult.violations && testResult.violations.length > 0 && (
                    <div className="space-y-2">
                      {testResult.violations.map((violation, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="text-red-500 flex-shrink-0 mt-0.5" size={16} />
                          <div>
                            <span className="font-medium">{violation.type}:</span>{' '}
                            <span className="text-gray-700">{violation.message}</span>
                            {violation.matched && (
                              <span className="ml-2 px-2 py-0.5 bg-red-100 rounded text-xs">
                                Matched: {violation.matched}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {testResult.sanitized_text && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-sm font-medium text-gray-700 mb-1">Sanitized Output:</p>
                      <p className="text-sm text-gray-600 bg-gray-100 p-2 rounded font-mono">
                        {testResult.sanitized_text}
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
                    {policies.map((policy) => (
                      <button
                        key={policy.id}
                        onClick={() => setSelectedPolicy(policy.id)}
                        className={`p-4 rounded-lg border-2 text-left transition-colors ${
                          selectedPolicy === policy.id
                            ? 'border-blue-600 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
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
                    ))}
                    {policies.length === 0 && (
                      <>
                        <button
                          onClick={() => setSelectedPolicy('strict')}
                          className={`p-4 rounded-lg border-2 text-left ${
                            selectedPolicy === 'strict' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                          }`}
                        >
                          <h4 className="font-medium">Strict</h4>
                          <p className="text-sm text-gray-600 mt-1">Maximum protection for regulated environments</p>
                        </button>
                        <button
                          onClick={() => setSelectedPolicy('balanced')}
                          className={`p-4 rounded-lg border-2 text-left ${
                            selectedPolicy === 'balanced' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                          }`}
                        >
                          <h4 className="font-medium">Balanced</h4>
                          <p className="text-sm text-gray-600 mt-1">Balance between safety and usability</p>
                        </button>
                        <button
                          onClick={() => setSelectedPolicy('permissive')}
                          className={`p-4 rounded-lg border-2 text-left ${
                            selectedPolicy === 'permissive' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                          }`}
                        >
                          <h4 className="font-medium">Permissive</h4>
                          <p className="text-sm text-gray-600 mt-1">Minimal restrictions for internal use</p>
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <button
                  onClick={updatePolicy}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
                >
                  <Save size={18} />
                  <span>{saving ? 'Saving...' : 'Save Policy'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
