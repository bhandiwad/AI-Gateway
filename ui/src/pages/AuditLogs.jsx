import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { 
  FileText, 
  Download, 
  AlertTriangle, 
  Search, 
  Filter, 
  RefreshCw,
  Shield,
  User,
  Key,
  Settings,
  LogIn,
  LogOut,
  Eye
} from 'lucide-react';

const eventTypeIcons = {
  login: LogIn,
  logout: LogOut,
  api_request: Key,
  config_change: Settings,
  guardrail_trigger: Shield,
  data_export: Download,
  user_created: User,
  user_updated: User,
  api_key_created: Key,
  api_key_revoked: Key,
};

const severityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export default function AuditLogs() {
  const { token } = useAuth();
  const [logs, setLogs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    event_type: '',
    start_date: '',
    end_date: '',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filters.event_type) params.append('event_type', filters.event_type);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      params.append('limit', '100');

      const [logsRes, summaryRes, securityRes] = await Promise.all([
        api.get(`/api/v1/admin/audit/logs?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/v1/admin/audit/summary', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        api.get('/api/v1/admin/audit/security-events?limit=10', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setLogs(logsRes.data.logs || []);
      setSummary(summaryRes.data);
      setSecurityEvents(securityRes.data.events || []);
    } catch (err) {
      console.error('Failed to fetch audit data:', err);
      setError('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      setExporting(true);
      const response = await api.post('/api/v1/admin/audit/export', {
        format,
        start_date: filters.start_date || null,
        end_date: filters.end_date || null,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export logs');
    } finally {
      setExporting(false);
    }
  };

  const applyFilters = () => {
    fetchData();
    setShowFilters(false);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const getEventIcon = (eventType) => {
    const Icon = eventTypeIcons[eventType] || FileText;
    return <Icon size={16} />;
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
            <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
            <p className="text-gray-600 mt-1">Compliance audit trail for regulatory requirements</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
            >
              <Filter size={18} />
              <span>Filters</span>
            </button>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 min-h-[44px]"
            >
              <RefreshCw size={18} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => handleExport('json')}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 min-h-[44px]"
            >
              <Download size={18} />
              <span>{exporting ? 'Exporting...' : 'Export'}</span>
            </button>
          </div>
        </div>

        {showFilters && (
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <h3 className="font-medium mb-4">Filter Logs</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
                <select
                  value={filters.event_type}
                  onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Events</option>
                  <option value="login">Login</option>
                  <option value="logout">Logout</option>
                  <option value="api_request">API Request</option>
                  <option value="config_change">Config Change</option>
                  <option value="guardrail_trigger">Guardrail Trigger</option>
                  <option value="data_export">Data Export</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={filters.start_date}
                  onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={filters.end_date}
                  onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setFilters({ event_type: '', start_date: '', end_date: '' })}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Clear
              </button>
              <button
                onClick={applyFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Apply Filters
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={20} />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-500">Total Events</p>
              <p className="text-2xl font-bold">{summary.total_events || 0}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-500">Security Events</p>
              <p className="text-2xl font-bold text-orange-600">{summary.security_events || 0}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-500">Guardrail Triggers</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.guardrail_triggers || 0}</p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-500">Config Changes</p>
              <p className="text-2xl font-bold text-blue-600">{summary.config_changes || 0}</p>
            </div>
          </div>
        )}

        {securityEvents.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="text-orange-600" size={20} />
              <h3 className="font-medium text-orange-800">Recent Security Events</h3>
            </div>
            <div className="space-y-2">
              {securityEvents.slice(0, 3).map((event, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-orange-700">{event.event_type}: {event.details?.reason || 'Security alert'}</span>
                  <span className="text-orange-500">{formatDate(event.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">User</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden lg:table-cell">IP Address</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                      No audit logs found
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">{getEventIcon(log.event_type)}</span>
                          <div>
                            <p className="font-medium text-gray-900">{log.event_type.replace(/_/g, ' ')}</p>
                            <p className="text-sm text-gray-500 truncate max-w-xs">{log.resource_type}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-gray-600">{log.user_id || 'System'}</span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-gray-500 font-mono text-sm">{log.ip_address || '-'}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-gray-500 text-sm">{formatDate(log.created_at)}</span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="text-blue-600 hover:text-blue-800 p-2"
                        >
                          <Eye size={18} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {selectedLog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
              <div className="p-4 border-b flex items-center justify-between">
                <h3 className="font-bold text-lg">Log Details</h3>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-gray-500 hover:text-gray-700 p-2"
                >
                  ×
                </button>
              </div>
              <div className="p-4">
                <dl className="space-y-3">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Event Type</dt>
                    <dd className="text-gray-900">{selectedLog.event_type}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Resource</dt>
                    <dd className="text-gray-900">{selectedLog.resource_type} ({selectedLog.resource_id || 'N/A'})</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">User ID</dt>
                    <dd className="text-gray-900">{selectedLog.user_id || 'System'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">IP Address</dt>
                    <dd className="text-gray-900 font-mono">{selectedLog.ip_address || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">User Agent</dt>
                    <dd className="text-gray-900 text-sm break-all">{selectedLog.user_agent || 'N/A'}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Timestamp</dt>
                    <dd className="text-gray-900">{formatDate(selectedLog.created_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Details</dt>
                    <dd className="text-gray-900">
                      <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
                        {JSON.stringify(selectedLog.details, null, 2)}
                      </pre>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
