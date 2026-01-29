import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/Header';
import { Save, User, Shield, Bell, Loader2, RefreshCw, Trash2, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

export default function Settings() {
  const { user, token, refreshUser } = useAuth();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [activeTab, setActiveTab] = useState('account');
  const [rateLimit, setRateLimit] = useState(user?.rate_limit || 100);
  const [monthlyBudgetINR, setMonthlyBudgetINR] = useState(Math.round((user?.monthly_budget || 0) * 83.5));
  
  const [ssoConfig, setSsoConfig] = useState(null);
  const [ssoLoading, setSsoLoading] = useState(true);
  const [ssoSaving, setSsoSaving] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [ssoMessage, setSsoMessage] = useState({ type: '', text: '' });
  
  const [ssoFormData, setSsoFormData] = useState({
    enabled: true,
    provider_name: '',
    client_id: '',
    client_secret: '',
    issuer_url: '',
    authorization_endpoint: '',
    token_endpoint: '',
    userinfo_endpoint: '',
    jwks_uri: '',
    scopes: 'openid profile email',
    user_id_claim: 'sub',
    email_claim: 'email',
    name_claim: 'name',
    auto_provision_users: true
  });

  useEffect(() => {
    if (activeTab === 'sso') {
      fetchSSOConfig();
    }
  }, [activeTab]);

  const fetchSSOConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/v1/admin/sso/config', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSsoConfig(response.data);
      setSsoFormData(prev => ({ ...prev, ...response.data }));
    } catch (err) {
      if (err.response?.status !== 404) {
        setSsoMessage({ type: 'error', text: 'Failed to load SSO configuration' });
      }
    } finally {
      setSsoLoading(false);
    }
  };

  const handleDiscoverOIDC = async () => {
    if (!ssoFormData.issuer_url) {
      setSsoMessage({ type: 'error', text: 'Please enter an issuer URL first' });
      return;
    }
    setDiscovering(true);
    setSsoMessage({ type: '', text: '' });
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('/api/v1/admin/sso/discover', 
        { issuer_url: ssoFormData.issuer_url },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSsoFormData(prev => ({ ...prev, ...response.data }));
      setSsoMessage({ type: 'success', text: 'OIDC endpoints discovered successfully' });
    } catch (err) {
      setSsoMessage({ type: 'error', text: err.response?.data?.detail || 'OIDC discovery failed' });
    } finally {
      setDiscovering(false);
    }
  };

  const handleSSOSave = async () => {
    setSsoSaving(true);
    setSsoMessage({ type: '', text: '' });
    try {
      const token = localStorage.getItem('token');
      const method = ssoConfig ? 'put' : 'post';
      await axios[method]('/api/v1/admin/sso/config', ssoFormData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSsoMessage({ type: 'success', text: 'SSO configuration saved successfully' });
      fetchSSOConfig();
    } catch (err) {
      setSsoMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to save SSO configuration' });
    } finally {
      setSsoSaving(false);
    }
  };

  const handleSSODelete = async () => {
    if (!confirm('Are you sure you want to delete the SSO configuration?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete('/api/v1/admin/sso/config', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSsoConfig(null);
      setSsoFormData({
        enabled: true, provider_name: '', client_id: '', client_secret: '',
        issuer_url: '', authorization_endpoint: '', token_endpoint: '',
        userinfo_endpoint: '', jwks_uri: '', scopes: 'openid profile email',
        user_id_claim: 'sub', email_claim: 'email', name_claim: 'name',
        auto_provision_users: true
      });
      setSsoMessage({ type: 'success', text: 'SSO configuration deleted' });
    } catch (err) {
      setSsoMessage({ type: 'error', text: 'Failed to delete SSO configuration' });
    }
  };

  const handleSSOChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSsoFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const monthlyBudgetUSD = monthlyBudgetINR / 83.5;
      await axios.put('/api/v1/admin/auth/me', {
        rate_limit: parseInt(rateLimit) || 0,
        monthly_budget: monthlyBudgetUSD
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      if (refreshUser) refreshUser();
    } catch (err) {
      setSaveError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Settings" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-4 mb-6 border-b border-gray-200">
            <button onClick={() => setActiveTab('account')} className={`pb-3 px-1 font-medium ${activeTab === 'account' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>Account</button>
            <button onClick={() => setActiveTab('sso')} className={`pb-3 px-1 font-medium ${activeTab === 'sso' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>SSO Configuration</button>
          </div>
          {activeTab === 'account' && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2"><User size={20} />Account Information</h3>
                <div className="space-y-4">
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">Name</label><input type="text" defaultValue={user?.name} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">Email</label><input type="email" defaultValue={user?.email} disabled className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500" /><p className="text-xs text-gray-400 mt-1">Email cannot be changed</p></div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2"><Shield size={20} />Security</h3>
                <div className="space-y-4">
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label><input type="password" placeholder="Enter current password" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">New Password</label><input type="password" placeholder="Enter new password" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2"><Bell size={20} />Notifications</h3>
                <div className="space-y-4">
                  <label className="flex items-center justify-between"><div><p className="font-medium text-gray-800">Budget Alerts</p><p className="text-sm text-gray-500">Get notified when approaching budget limit</p></div><input type="checkbox" defaultChecked className="w-5 h-5 text-blue-600" /></label>
                  <label className="flex items-center justify-between"><div><p className="font-medium text-gray-800">Usage Reports</p><p className="text-sm text-gray-500">Weekly usage summary emails</p></div><input type="checkbox" defaultChecked className="w-5 h-5 text-blue-600" /></label>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Account Limits</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Rate Limit (requests/min)</label>
                    <input type="number" value={rateLimit} onChange={(e) => setRateLimit(e.target.value)} min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <p className="text-xs text-gray-500 mt-1">Maximum API requests per minute (0 = unlimited)</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Budget (₹)</label>
                    <input type="number" value={monthlyBudgetINR} onChange={(e) => setMonthlyBudgetINR(e.target.value)} min="0" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <p className="text-xs text-gray-500 mt-1">Maximum monthly spending limit in INR (0 = no limit)</p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Current Usage:</span>
                      <span className="ml-2 font-medium text-gray-800">{user?.current_spend ? `₹${(user.current_spend * 83.5).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '₹0'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Budget Remaining:</span>
                      <span className="ml-2 font-medium text-green-600">₹{((user?.monthly_budget - (user?.current_spend || 0)) * 83.5).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                    </div>
                  </div>
                </div>
              </div>
              {saveError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {saveError}
                </div>
              )}
              <div className="flex justify-end"><button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">{saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}{saving ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}</button></div>
            </div>
          )}
          {activeTab === 'sso' && (
            <div className="space-y-6">
              {ssoMessage.text && (<div className={`p-4 rounded-lg flex items-center gap-2 ${ssoMessage.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{ssoMessage.type === 'success' ? <CheckCircle size={20} /> : <XCircle size={20} />}{ssoMessage.text}</div>)}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><Shield className="text-blue-600" size={24} /></div><div><h2 className="text-lg font-semibold text-gray-900">Single Sign-On (SSO)</h2><p className="text-sm text-gray-500">Configure OIDC-based SSO for your identity provider</p></div></div></div>
                {ssoLoading ? (<div className="p-6 flex justify-center"><Loader2 className="animate-spin" size={32} /></div>) : (
                  <div className="p-6 space-y-6">
                    <div className="flex items-center gap-3"><input type="checkbox" id="enabled" name="enabled" checked={ssoFormData.enabled} onChange={handleSSOChange} className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500" /><label htmlFor="enabled" className="text-sm font-medium text-gray-700">Enable SSO</label></div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Provider Name</label><input type="text" name="provider_name" value={ssoFormData.provider_name} onChange={handleSSOChange} placeholder="e.g., okta, auth0, azure-ad" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /><p className="mt-1 text-xs text-gray-500">Users enter this to initiate SSO login</p></div>
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Issuer URL</label><div className="flex gap-2"><input type="url" name="issuer_url" value={ssoFormData.issuer_url} onChange={handleSSOChange} placeholder="https://your-domain.okta.com" className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /><button type="button" onClick={handleDiscoverOIDC} disabled={discovering} className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 flex items-center gap-1">{discovering ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}Discover</button></div></div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label><input type="text" name="client_id" value={ssoFormData.client_id} onChange={handleSSOChange} placeholder="Your OIDC client ID" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Client Secret</label><input type="password" name="client_secret" value={ssoFormData.client_secret} onChange={handleSSOChange} placeholder="Your OIDC client secret" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                    </div>
                    <div className="border-t border-gray-200 pt-4"><h3 className="text-sm font-medium text-gray-700 mb-3">OIDC Endpoints (auto-discovered)</h3><div className="grid grid-cols-1 md:grid-cols-2 gap-4"><div><label className="block text-sm text-gray-600 mb-1">Authorization Endpoint</label><input type="url" name="authorization_endpoint" value={ssoFormData.authorization_endpoint} onChange={handleSSOChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" /></div><div><label className="block text-sm text-gray-600 mb-1">Token Endpoint</label><input type="url" name="token_endpoint" value={ssoFormData.token_endpoint} onChange={handleSSOChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" /></div><div><label className="block text-sm text-gray-600 mb-1">Userinfo Endpoint</label><input type="url" name="userinfo_endpoint" value={ssoFormData.userinfo_endpoint} onChange={handleSSOChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" /></div><div><label className="block text-sm text-gray-600 mb-1">JWKS URI</label><input type="url" name="jwks_uri" value={ssoFormData.jwks_uri} onChange={handleSSOChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" /></div></div></div>
                    <div><label className="block text-sm font-medium text-gray-700 mb-1">Scopes</label><input type="text" name="scopes" value={ssoFormData.scopes} onChange={handleSSOChange} placeholder="openid profile email" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" /></div>
                    <div className="flex items-center gap-3"><input type="checkbox" id="auto_provision_users" name="auto_provision_users" checked={ssoFormData.auto_provision_users} onChange={handleSSOChange} className="h-4 w-4 text-blue-600 rounded focus:ring-blue-500" /><label htmlFor="auto_provision_users" className="text-sm font-medium text-gray-700">Auto-provision users on first SSO login</label></div>
                  </div>
                )}
                <div className="p-6 border-t border-gray-200 flex justify-between">{ssoConfig && (<button type="button" onClick={handleSSODelete} className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2"><Trash2 size={18} />Delete Configuration</button>)}<div className="flex gap-3 ml-auto"><button type="button" onClick={handleSSOSave} disabled={ssoSaving} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">{ssoSaving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}Save Configuration</button></div></div>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg"><h3 className="font-medium text-blue-900 mb-2">Setup Instructions</h3><ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside"><li>Create an OIDC application in your identity provider (Okta, Auth0, Azure AD, etc.)</li><li>Set the callback URL to: <code className="bg-blue-100 px-1 rounded">{window.location.origin}/login</code></li><li>Copy the Client ID and Client Secret from your identity provider</li><li>Enter the Issuer URL and click "Discover" to auto-populate endpoints</li><li>Save the configuration and test SSO login from the login page</li></ol></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
