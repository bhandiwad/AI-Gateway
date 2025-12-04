import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, CheckCircle, XCircle, Clock, Zap, TrendingUp, RefreshCw } from 'lucide-react';

const HealthDashboard = () => {
  const [healthData, setHealthData] = useState(null);
  const [circuitBreakers, setCircuitBreakers] = useState({});
  const [loadBalancerStats, setLoadBalancerStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealthData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch health dashboard
      const dashboardRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/health-dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const dashboard = await dashboardRes.json();
      setHealthData(dashboard);

      // Fetch circuit breakers
      const cbRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const cb = await cbRes.json();
      setCircuitBreakers(cb);

      // Fetch load balancer stats
      const lbRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/load-balancer/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const lb = await lbRes.json();
      setLoadBalancerStats(lb);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching health data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    const interval = autoRefresh ? setInterval(fetchHealthData, 10000) : null;
    return () => interval && clearInterval(interval);
  }, [autoRefresh]);

  const getStateColor = (state) => {
    switch (state?.toLowerCase()) {
      case 'closed': return 'text-green-600 bg-green-100';
      case 'open': return 'text-red-600 bg-red-100';
      case 'half_open': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStateIcon = (state) => {
    switch (state?.toLowerCase()) {
      case 'closed': return <CheckCircle className="w-5 h-5" />;
      case 'open': return <XCircle className="w-5 h-5" />;
      case 'half_open': return <AlertCircle className="w-5 h-5" />;
      default: return <Clock className="w-5 h-5" />;
    }
  };

  const forceCircuitState = async (provider, action) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers/${provider}/force-${action}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      fetchHealthData();
    } catch (error) {
      console.error('Error updating circuit breaker:', error);
    }
  };

  const resetCircuitBreaker = async (provider) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/admin/router/circuit-breakers/${provider}/reset`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      fetchHealthData();
    } catch (error) {
      console.error('Error resetting circuit breaker:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const providers = healthData?.providers || [];
  const summary = circuitBreakers?.summary || {};

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-7 h-7 text-blue-600" />
            Provider Health Dashboard
          </h1>
          <p className="text-gray-600 mt-1">Real-time monitoring of load balancers and circuit breakers</p>
        </div>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300"
            />
            Auto-refresh (10s)
          </label>
          <button
            onClick={fetchHealthData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Now
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Providers</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total || 0}</p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Healthy (Closed)</p>
              <p className="text-2xl font-bold text-green-600">{summary.closed || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Unhealthy (Open)</p>
              <p className="text-2xl font-bold text-red-600">{summary.open || 0}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Testing (Half-Open)</p>
              <p className="text-2xl font-bold text-yellow-600">{summary.half_open || 0}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Provider Cards */}
      <div className="space-y-4">
        {providers.map((provider) => {
          const circuitBreaker = provider.circuit_breaker || {};
          const groups = provider.groups || [];

          return (
            <div key={provider.name} className="bg-white rounded-lg shadow-lg overflow-hidden">
              {/* Provider Header */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-gray-900">{provider.name}</h2>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1 ${getStateColor(circuitBreaker.state)}`}>
                      {getStateIcon(circuitBreaker.state)}
                      {circuitBreaker.state?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {circuitBreaker.state === 'open' && (
                      <button
                        onClick={() => forceCircuitState(provider.name, 'close')}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                      >
                        Force Close
                      </button>
                    )}
                    {circuitBreaker.state === 'closed' && (
                      <button
                        onClick={() => forceCircuitState(provider.name, 'open')}
                        className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                      >
                        Force Open
                      </button>
                    )}
                    <button
                      onClick={() => resetCircuitBreaker(provider.name)}
                      className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-4">
                {/* Circuit Breaker Metrics */}
                {circuitBreaker && Object.keys(circuitBreaker).length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Circuit Breaker Metrics
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Failures</p>
                        <p className="text-lg font-semibold text-red-600">{circuitBreaker.failure_count || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Successes</p>
                        <p className="text-lg font-semibold text-green-600">{circuitBreaker.success_count || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Consecutive Failures</p>
                        <p className="text-lg font-semibold text-orange-600">{circuitBreaker.consecutive_failures || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-xs text-gray-600">Rejected Requests</p>
                        <p className="text-lg font-semibold text-red-600">{circuitBreaker.rejected_requests || 0}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Load Balancer Groups */}
                {groups.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Load Balancer Groups ({groups.length})
                    </h3>
                    <div className="space-y-2">
                      {groups.map((group) => (
                        <div key={group.group} className="bg-gray-50 p-3 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">{group.group}</span>
                            <span className={`text-xs px-2 py-1 rounded ${group.is_healthy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {group.is_healthy ? 'Healthy' : 'Unhealthy'}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                            <div>
                              <p className="text-xs text-gray-600">Weight</p>
                              <p className="font-semibold">{group.weight}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Active Requests</p>
                              <p className="font-semibold text-blue-600">{group.active_requests}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Total Requests</p>
                              <p className="font-semibold">{group.total_requests}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-600">Avg Latency</p>
                              <p className="font-semibold text-purple-600">{group.avg_latency_ms?.toFixed(0) || 0}ms</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {groups.length === 0 && (!circuitBreaker || Object.keys(circuitBreaker).length === 0) && (
                  <p className="text-gray-500 text-sm italic">No metrics available for this provider</p>
                )}
              </div>
            </div>
          );
        })}

        {providers.length === 0 && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Providers Configured</h3>
            <p className="text-gray-600">Configure providers to start monitoring health and performance.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HealthDashboard;
