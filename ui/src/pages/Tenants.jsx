import { useState, useEffect } from 'react';
import { tenantsApi } from '../api/client';
import Header from '../components/Header';
import { Users, Search, Edit2, CheckCircle, XCircle } from 'lucide-react';

export default function Tenants() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const response = await tenantsApi.list();
      setTenants(response.data);
    } catch (error) {
      console.error('Failed to load tenants:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (tenant) => {
    setEditingId(tenant.id);
    setEditData({
      rate_limit: tenant.rate_limit,
      monthly_budget: tenant.monthly_budget,
      is_active: tenant.is_active
    });
  };

  const handleSave = async (id) => {
    try {
      await tenantsApi.update(id, editData);
      setTenants(tenants.map(t => t.id === id ? { ...t, ...editData } : t));
      setEditingId(null);
    } catch (error) {
      console.error('Failed to update tenant:', error);
    }
  };

  const filteredTenants = tenants.filter(tenant =>
    tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Tenant Management" />
      
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <p className="text-gray-500">
              Manage tenant accounts and their settings
            </p>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tenants..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tenant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rate Limit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Budget
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Spend
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredTenants.map((tenant) => (
                    <tr key={tenant.id}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-blue-600 font-medium">
                              {tenant.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-gray-800">{tenant.name}</p>
                            <p className="text-sm text-gray-500">{tenant.email}</p>
                          </div>
                          {tenant.is_admin && (
                            <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                              Admin
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {editingId === tenant.id ? (
                          <select
                            value={editData.is_active ? 'active' : 'inactive'}
                            onChange={(e) => setEditData({
                              ...editData,
                              is_active: e.target.value === 'active'
                            })}
                            className="px-2 py-1 border border-gray-300 rounded"
                          >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                        ) : tenant.is_active ? (
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle size={16} />
                            Active
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-red-600">
                            <XCircle size={16} />
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {editingId === tenant.id ? (
                          <input
                            type="number"
                            value={editData.rate_limit}
                            onChange={(e) => setEditData({
                              ...editData,
                              rate_limit: parseInt(e.target.value)
                            })}
                            className="w-24 px-2 py-1 border border-gray-300 rounded"
                          />
                        ) : (
                          <span className="text-gray-800">{tenant.rate_limit}/min</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {editingId === tenant.id ? (
                          <input
                            type="number"
                            value={editData.monthly_budget}
                            onChange={(e) => setEditData({
                              ...editData,
                              monthly_budget: parseFloat(e.target.value)
                            })}
                            className="w-24 px-2 py-1 border border-gray-300 rounded"
                          />
                        ) : (
                          <span className="text-gray-800">₹{((tenant.monthly_budget || 0) * 83.5).toLocaleString('en-IN')}</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-gray-800">
                          ₹{((tenant.current_spend || 0) * 83.5).toLocaleString('en-IN', {maximumFractionDigits: 0})}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {editingId === tenant.id ? (
                          <div className="flex gap-2 justify-end">
                            <button
                              onClick={() => handleSave(tenant.id)}
                              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleEdit(tenant)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <Edit2 size={18} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredTenants.length === 0 && (
                <div className="text-center py-12">
                  <Users className="mx-auto text-gray-300 mb-4" size={48} />
                  <p className="text-gray-500">No tenants found</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
