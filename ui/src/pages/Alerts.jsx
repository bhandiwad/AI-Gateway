import React, { useState, useEffect } from 'react';
import { Bell, Plus, Edit2, Trash2, Mail, MessageSquare, Webhook, Activity, AlertTriangle, CheckCircle, Info } from 'lucide-react';

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
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="w-7 h-7 text-blue-600" />
            Alert Configuration
          </h1>
          <p className="text-gray-600 mt-1">Configure notifications for important events</p>
        </div>
        <button
          onClick={() => {
            setEditingConfig(null);
            setShowModal(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
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
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Bell className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Alert Configurations</h3>
          <p className="text-gray-600 mb-4">Get notified when important events occur in your gateway.</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
              <div key={config.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Icon className="w-5 h-5 text-gray-600" />
                        <h3 className="text-lg font-semibold text-gray-900">{config.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${severityColors[config.severity]}`}>
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
                          <span className="text-gray-600">Type:</span>
                          <span className="ml-2 font-medium">{alertType?.label || config.alert_type}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Cooldown:</span>
                          <span className="ml-2 font-medium">{config.cooldown_minutes} min</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Max/hour:</span>
                          <span className="ml-2 font-medium">{config.max_alerts_per_hour}</span>
                        </div>
                      </div>

                      <div className="flex gap-2 mt-3">
                        {config.channels.map((channel) => (
                          <span
                            key={channel}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                          >
                            {getChannelIcon(channel)}
                            {channel}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => {
                          setEditingConfig(config);
                          setShowModal(true);
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteConfig(config.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
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

      {/* Modal for creating/editing alert */}
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
  );
};

// Alert Modal Component
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">
            {config ? 'Edit' : 'Create'} Alert Configuration
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                rows="2"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Alert Type</label>
                <select
                  value={formData.alert_type}
                  onChange={(e) => setFormData({ ...formData, alert_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {alertTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Severity</label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Notification Channels</label>
              <div className="grid grid-cols-2 gap-2">
                {['in_app', 'email', 'slack', 'webhook'].map((channel) => (
                  <label key={channel} className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={formData.channels.includes(channel)}
                      onChange={() => toggleChannel(channel)}
                      className="rounded"
                    />
                    <span className="capitalize">{channel.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Cooldown (minutes)</label>
                <input
                  type="number"
                  value={formData.cooldown_minutes}
                  onChange={(e) => setFormData({ ...formData, cooldown_minutes: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Max alerts per hour</label>
                <input
                  type="number"
                  value={formData.max_alerts_per_hour}
                  onChange={(e) => setFormData({ ...formData, max_alerts_per_hour: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                  min="1"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="group_similar"
                checked={formData.group_similar}
                onChange={(e) => setFormData({ ...formData, group_similar: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="group_similar" className="text-sm">Group similar alerts</label>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
