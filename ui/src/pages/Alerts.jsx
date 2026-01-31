import React, { useState, useEffect } from 'react';
import { Bell, Plus, Edit2, Trash2, Mail, MessageSquare, Webhook, Activity, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import Header from '../components/Header';

const Alerts = () => {
  const [alertConfigs, setAlertConfigs] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  const alertTypes = [
    { value: 'circuit_breaker_opened', label: 'Circuit Breaker Opened', icon: AlertTriangle },
    { value: 'circuit_breaker_closed', label: 'Circuit Breaker Closed', icon: CheckCircle },
    { value: 'provider_unhealthy', label: 'Provider Unhealthy', icon: AlertTriangle },
    { value: 'provider_recovered', label: 'Provider Recovered', icon: CheckCircle },
    { value: 'cost_limit_warning', label: 'Cost Limit Warning (90%)', icon: Info },
    { value: 'cost_limit_exceeded', label: 'Cost Limit Exceeded', icon: AlertTriangle },
    { value: 'rate_limit_warning', label: 'Rate Limit Warning', icon: Info },
    { value: 'rate_limit_exceeded', label: 'Rate Limit Exceeded', icon: AlertTriangle },
    { value: 'high_error_rate', label: 'High Error Rate', icon: AlertTriangle },
    { value: 'high_latency', label: 'High Latency', icon: AlertTriangle },
    { value: 'quota_exhausted', label: 'Provider Quota Exhausted', icon: AlertTriangle },
  ];

  const severityColors = {
    info: 'bg-blue-100 text-blue-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };

  useEffect(() => {
    fetchAlertConfigs();
  }, []);

  const fetchAlertConfigs = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/alerts/configs`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const data = await res.json();
      setAlertConfigs(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching alert configs:', error);
      setLoading(false);
    }
  };

  const deleteConfig = async (id) => {
    if (!confirm('Are you sure you want to delete this alert configuration?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/alerts/configs/${id}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      fetchAlertConfigs();
    } catch (error) {
      console.error('Error deleting config:', error);
    }
  };

  const toggleActive = async (config) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/alerts/configs/${config.id}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ is_active: !config.is_active })
        }
      );
      fetchAlertConfigs();
    } catch (error) {
      console.error('Error toggling config:', error);
    }
  };

  const getChannelIcon = (channel) => {
    switch (channel) {
      case 'email': return <Mail className="w-4 h-4" />;
      case 'slack': return <MessageSquare className="w-4 h-4" />;
      case 'webhook': return <Webhook className="w-4 h-4" />;
      case 'in_app': return <Bell className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Alerts" />
      
      <div className="flex-1 overflow-auto p-4 sm:p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
                <div className="p-2 bg-lime-100 rounded-lg">
                  <Bell className="w-6 h-6 text-lime-700" />
                </div>
                Alert Configuration
              </h1>
              <p className="text-gray-600 mt-1 text-sm">Configure notifications for important events</p>
            </div>
            <button
              onClick={() => {
                setEditingConfig(null);
                setShowModal(true);
              }}
              className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 flex items-center gap-2 text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Alert
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : alertConfigs.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bell className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Alert Configurations</h3>
              <p className="text-gray-600 mb-6">Get notified when important events occur in your gateway.</p>
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium transition-colors"
              >
                Create Your First Alert
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {alertConfigs.map((config) => {
                const alertType = alertTypes.find(t => t.value === config.alert_type);
                const Icon = alertType?.icon || Bell;

                return (
                  <div key={config.id} className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                    <div className="p-4 sm:p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-3 mb-2">
                            <div className="p-1.5 bg-gray-100 rounded-lg">
                              <Icon className="w-5 h-5 text-gray-600" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900">{config.name}</h3>
                            <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${severityColors[config.severity]}`}>
                              {config.severity.toUpperCase()}
                            </span>
                            <label className="flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={config.is_active}
                                onChange={() => toggleActive(config)}
                                className="sr-only peer"
                              />
                              <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                          </div>
                          
                          {config.description && (
                            <p className="text-sm text-gray-600 mb-3">{config.description}</p>
                          )}

                          <div className="flex flex-wrap gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">Type:</span>
                              <span className="ml-2 font-medium text-gray-700">{alertType?.label || config.alert_type}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Cooldown:</span>
                              <span className="ml-2 font-medium text-gray-700">{config.cooldown_minutes} min</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Max/hour:</span>
                              <span className="ml-2 font-medium text-gray-700">{config.max_alerts_per_hour}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-2 mt-3">
                            {config.channels.map((channel) => (
                              <span
                                key={channel}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg"
                              >
                                {getChannelIcon(channel)}
                                {channel.replace('_', ' ')}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="flex gap-2 flex-shrink-0">
                          <button
                            onClick={() => {
                              setEditingConfig(config);
                              setShowModal(true);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteConfig(config.id)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {showModal && (
            <AlertModal
              config={editingConfig}
              alertTypes={alertTypes}
              onClose={() => {
                setShowModal(false);
                setEditingConfig(null);
              }}
              onSave={() => {
                setShowModal(false);
                setEditingConfig(null);
                fetchAlertConfigs();
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

const AlertModal = ({ config, alertTypes, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: config?.name || '',
    description: config?.description || '',
    alert_type: config?.alert_type || 'circuit_breaker_opened',
    severity: config?.severity || 'warning',
    channels: config?.channels || ['in_app'],
    channel_config: config?.channel_config || {},
    cooldown_minutes: config?.cooldown_minutes || 15,
    max_alerts_per_hour: config?.max_alerts_per_hour || 10,
    conditions: config?.conditions || {},
    group_similar: config?.group_similar !== undefined ? config.group_similar : true,
  });

  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const token = localStorage.getItem('token');
      const url = config
        ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/alerts/configs/${config.id}`
        : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/alerts/configs`;

      const method = config ? 'PUT' : 'POST';

      await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      onSave();
    } catch (error) {
      console.error('Error saving alert config:', error);
      alert('Failed to save alert configuration');
    } finally {
      setSaving(false);
    }
  };

  const toggleChannel = (channel) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {config ? 'Edit' : 'Create'} Alert Configuration
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                rows="2"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Alert Type</label>
                <select
                  value={formData.alert_type}
                  onChange={(e) => setFormData({ ...formData, alert_type: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  {alertTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Severity</label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Notification Channels</label>
              <div className="grid grid-cols-2 gap-2">
                {['in_app', 'email', 'slack', 'webhook'].map((channel) => (
                  <label key={channel} className="flex items-center gap-2.5 p-3 border border-gray-200 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes(channel)}
                      onChange={() => toggleChannel(channel)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="capitalize text-sm font-medium text-gray-700">{channel.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>

              {formData.channels.includes('email') && (
                <div className="mt-3 p-3 bg-gray-50 rounded-xl">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Recipients</label>
                  <input
                    type="text"
                    value={formData.channel_config?.email?.recipients?.join(', ') || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      channel_config: {
                        ...formData.channel_config,
                        email: { recipients: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                      }
                    })}
                    placeholder="email1@example.com, email2@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Comma-separated email addresses</p>
                </div>
              )}

              {formData.channels.includes('slack') && (
                <div className="mt-3 p-3 bg-gray-50 rounded-xl">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Slack Webhook URL</label>
                  <input
                    type="url"
                    value={formData.channel_config?.slack?.webhook_url || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      channel_config: {
                        ...formData.channel_config,
                        slack: { webhook_url: e.target.value }
                      }
                    })}
                    placeholder="https://hooks.slack.com/services/..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Create an incoming webhook in your Slack workspace</p>
                </div>
              )}

              {formData.channels.includes('webhook') && (
                <div className="mt-3 p-3 bg-gray-50 rounded-xl">
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Webhook URL</label>
                  <input
                    type="url"
                    value={formData.channel_config?.webhook?.url || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      channel_config: {
                        ...formData.channel_config,
                        webhook: { ...formData.channel_config?.webhook, url: e.target.value }
                      }
                    })}
                    placeholder="https://your-api.com/webhook"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Your custom webhook endpoint to receive alert payloads</p>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Cooldown (minutes)</label>
                <input
                  type="number"
                  value={formData.cooldown_minutes}
                  onChange={(e) => setFormData({ ...formData, cooldown_minutes: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Max alerts per hour</label>
                <input
                  type="number"
                  value={formData.max_alerts_per_hour}
                  onChange={(e) => setFormData({ ...formData, max_alerts_per_hour: parseInt(e.target.value) })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  min="1"
                />
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <input
                type="checkbox"
                id="group_similar"
                checked={formData.group_similar}
                onChange={(e) => setFormData({ ...formData, group_similar: e.target.checked })}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="group_similar" className="text-sm font-medium text-gray-700">Group similar alerts</label>
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
                className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium disabled:opacity-50 transition-colors"
                disabled={saving}
              >
                {saving ? 'Saving...' : config ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Alerts;
