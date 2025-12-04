import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Building2, Users, Plus, Edit2, Trash2, UserPlus, UserMinus, TrendingUp, DollarSign } from 'lucide-react';
import Header from '../components/Header';

export default function Organization() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('departments');
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [users, setUsers] = useState([]);
  const [orgStats, setOrgStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);
  const [showTeamModal, setShowTeamModal] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState(null);
  const [editingTeam, setEditingTeam] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [deptRes, teamRes, userRes, statsRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/admin/organization/departments', { headers }),
        fetch('http://localhost:8000/api/v1/admin/organization/teams', { headers }),
        fetch('http://localhost:8000/api/v1/admin/users', { headers }),
        fetch('http://localhost:8000/api/v1/admin/organization/stats', { headers })
      ]);

      if (deptRes.ok) setDepartments(await deptRes.json());
      if (teamRes.ok) setTeams(await teamRes.json());
      if (userRes.ok) setUsers(await userRes.json());
      if (statsRes.ok) setOrgStats(await statsRes.json());
    } catch (error) {
      console.error('Failed to load organization data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createDepartment = async (data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/admin/organization/departments', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadData();
        setShowDepartmentModal(false);
        setEditingDepartment(null);
      }
    } catch (error) {
      console.error('Failed to create department:', error);
    }
  };

  const updateDepartment = async (id, data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/organization/departments/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadData();
        setShowDepartmentModal(false);
        setEditingDepartment(null);
      }
    } catch (error) {
      console.error('Failed to update department:', error);
    }
  };

  const deleteDepartment = async (id) => {
    if (!confirm('Are you sure you want to delete this department?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/organization/departments/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadData();
      }
    } catch (error) {
      console.error('Failed to delete department:', error);
    }
  };

  const createTeam = async (data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/admin/organization/teams', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadData();
        setShowTeamModal(false);
        setEditingTeam(null);
      }
    } catch (error) {
      console.error('Failed to create team:', error);
    }
  };

  const updateTeam = async (id, data) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/organization/teams/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await loadData();
        setShowTeamModal(false);
        setEditingTeam(null);
      }
    } catch (error) {
      console.error('Failed to update team:', error);
    }
  };

  const deleteTeam = async (id) => {
    if (!confirm('Are you sure you want to delete this team?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/admin/organization/teams/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadData();
      }
    } catch (error) {
      console.error('Failed to delete team:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-h-0">
        <Header title="Organization" />
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-lime-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Organization" />
      <div className="flex-1 overflow-auto p-4 md:p-6 lg:p-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 flex items-center gap-3">
              <div className="p-2 bg-lime-100 rounded-lg">
                <Building2 className="w-6 h-6 text-lime-700" />
              </div>
              Organization
            </h1>
            <p className="text-gray-600 mt-1">Manage departments, teams, and organizational structure</p>
          </div>

          {/* Organization Stats */}
          {orgStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Departments</p>
                    <p className="text-2xl font-bold text-gray-900">{orgStats.total_departments}</p>
                  </div>
                  <div className="p-3 bg-lime-100 rounded-lg">
                    <Building2 className="w-6 h-6 text-lime-700" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Teams</p>
                    <p className="text-2xl font-bold text-gray-900">{orgStats.total_teams}</p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-lg">
                    <Users className="w-6 h-6 text-green-700" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Monthly Spend</p>
                    <p className="text-2xl font-bold text-gray-900">₹{orgStats.total_spend_month.toFixed(2)}</p>
                  </div>
                  <div className="p-3 bg-emerald-100 rounded-lg">
                    <DollarSign className="w-6 h-6 text-emerald-700" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Budget Utilization</p>
                    <p className="text-2xl font-bold text-gray-900">{orgStats.budget_utilization.toFixed(1)}%</p>
                  </div>
                  <div className="p-3 bg-teal-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-teal-700" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px">
                <button
                  onClick={() => setActiveTab('departments')}
                  className={`px-6 py-4 text-sm font-medium border-b-2 ${
                    activeTab === 'departments'
                      ? 'border-lime-600 text-lime-700'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }`}
                >
                  <Building2 className="w-4 h-4 inline mr-2" />
                  Departments
                </button>
                <button
                  onClick={() => setActiveTab('teams')}
                  className={`px-6 py-4 text-sm font-medium border-b-2 ${
                    activeTab === 'teams'
                      ? 'border-lime-600 text-lime-700'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }`}
                >
                  <Users className="w-4 h-4 inline mr-2" />
                  Teams
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'departments' && (
                <DepartmentsTab
                  departments={departments}
                  users={users}
                  onAdd={() => {
                    setEditingDepartment(null);
                    setShowDepartmentModal(true);
                  }}
                  onEdit={(dept) => {
                    setEditingDepartment(dept);
                    setShowDepartmentModal(true);
                  }}
                  onDelete={deleteDepartment}
                />
              )}

              {activeTab === 'teams' && (
                <TeamsTab
                  teams={teams}
                  departments={departments}
                  users={users}
                  onAdd={() => {
                    setEditingTeam(null);
                    setShowTeamModal(true);
                  }}
                  onEdit={(team) => {
                    setEditingTeam(team);
                    setShowTeamModal(true);
                  }}
                  onDelete={deleteTeam}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Department Modal */}
      {showDepartmentModal && (
        <DepartmentModal
          department={editingDepartment}
          users={users}
          onClose={() => {
            setShowDepartmentModal(false);
            setEditingDepartment(null);
          }}
          onSave={(data) => {
            if (editingDepartment) {
              updateDepartment(editingDepartment.id, data);
            } else {
              createDepartment(data);
            }
          }}
        />
      )}

      {/* Team Modal */}
      {showTeamModal && (
        <TeamModal
          team={editingTeam}
          departments={departments}
          users={users}
          onClose={() => {
            setShowTeamModal(false);
            setEditingTeam(null);
          }}
          onSave={(data) => {
            if (editingTeam) {
              updateTeam(editingTeam.id, data);
            } else {
              createTeam(data);
            }
          }}
        />
      )}
    </div>
  );
}

function DepartmentsTab({ departments, users, onAdd, onEdit, onDelete }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Departments</h2>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Department
        </button>
      </div>

      {departments.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No departments yet</p>
          <button
            onClick={onAdd}
            className="mt-4 text-lime-600 hover:text-lime-700 font-medium"
          >
            Create your first department
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {departments.map((dept) => (
            <div key={dept.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">{dept.name}</h3>
                  {dept.code && <p className="text-sm text-gray-500">Code: {dept.code}</p>}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(dept)}
                    className="p-1 text-gray-600 hover:text-lime-600"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(dept.id)}
                    className="p-1 text-gray-600 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {dept.description && (
                <p className="text-sm text-gray-600 mb-3">{dept.description}</p>
              )}

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-gray-500">Budget (Monthly)</p>
                  <p className="font-medium">₹{dept.budget_monthly || 0}</p>
                </div>
                <div>
                  <p className="text-gray-500">Current Spend</p>
                  <p className="font-medium">₹{dept.current_spend || 0}</p>
                </div>
              </div>

              {dept.manager_user_id && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500">Manager</p>
                  <p className="text-sm font-medium">
                    {users.find(u => u.id === dept.manager_user_id)?.name || 'Unknown'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TeamsTab({ teams, departments, users, onAdd, onEdit, onDelete }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Teams</h2>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Team
        </button>
      </div>

      {teams.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p>No teams yet</p>
          <button
            onClick={onAdd}
            className="mt-4 text-lime-600 hover:text-lime-700 font-medium"
          >
            Create your first team
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((team) => (
            <div key={team.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">{team.name}</h3>
                  {team.code && <p className="text-sm text-gray-500">Code: {team.code}</p>}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(team)}
                    className="p-1 text-gray-600 hover:text-lime-600"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDelete(team.id)}
                    className="p-1 text-gray-600 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {team.description && (
                <p className="text-sm text-gray-600 mb-3">{team.description}</p>
              )}

              {team.department_id && (
                <div className="mb-2">
                  <p className="text-xs text-gray-500">Department</p>
                  <p className="text-sm font-medium">
                    {departments.find(d => d.id === team.department_id)?.name || 'Unknown'}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                <div>
                  <p className="text-gray-500">Budget</p>
                  <p className="font-medium">₹{team.budget_monthly || 0}</p>
                </div>
                <div>
                  <p className="text-gray-500">Spend</p>
                  <p className="font-medium">₹{team.current_spend || 0}</p>
                </div>
              </div>

              {team.lead_user_id && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500">Team Lead</p>
                  <p className="text-sm font-medium">
                    {users.find(u => u.id === team.lead_user_id)?.name || 'Unknown'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DepartmentModal({ department, users, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: department?.name || '',
    code: department?.code || '',
    description: department?.description || '',
    budget_monthly: department?.budget_monthly || '',
    budget_yearly: department?.budget_yearly || '',
    cost_center: department?.cost_center || '',
    manager_user_id: department?.manager_user_id || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...formData };
    if (data.budget_monthly) data.budget_monthly = parseFloat(data.budget_monthly);
    if (data.budget_yearly) data.budget_yearly = parseFloat(data.budget_yearly);
    if (data.manager_user_id) data.manager_user_id = parseInt(data.manager_user_id);
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {department ? 'Edit Department' : 'Create Department'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Cost Center</label>
                <input
                  type="text"
                  value={formData.cost_center}
                  onChange={(e) => setFormData({ ...formData, cost_center: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Monthly Budget (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget_monthly}
                  onChange={(e) => setFormData({ ...formData, budget_monthly: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Yearly Budget (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget_yearly}
                  onChange={(e) => setFormData({ ...formData, budget_yearly: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Manager</label>
              <select
                value={formData.manager_user_id}
                onChange={(e) => setFormData({ ...formData, manager_user_id: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              >
                <option value="">Select manager</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
              >
                {department ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function TeamModal({ team, departments, users, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: team?.name || '',
    code: team?.code || '',
    description: team?.description || '',
    department_id: team?.department_id || '',
    budget_monthly: team?.budget_monthly || '',
    lead_user_id: team?.lead_user_id || '',
    tags: team?.tags?.join(', ') || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = { ...formData };
    if (data.budget_monthly) data.budget_monthly = parseFloat(data.budget_monthly);
    if (data.department_id) data.department_id = parseInt(data.department_id);
    if (data.lead_user_id) data.lead_user_id = parseInt(data.lead_user_id);
    if (data.tags) {
      data.tags = data.tags.split(',').map(t => t.trim()).filter(t => t);
    } else {
      data.tags = [];
    }
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {team ? 'Edit Team' : 'Create Team'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Department</label>
                <select
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                >
                  <option value="">Select department</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Monthly Budget (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.budget_monthly}
                  onChange={(e) => setFormData({ ...formData, budget_monthly: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Team Lead</label>
                <select
                  value={formData.lead_user_id}
                  onChange={(e) => setFormData({ ...formData, lead_user_id: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
                >
                  <option value="">Select team lead</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} ({user.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Tags (comma-separated)</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="e.g., backend, frontend, devops"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-colors"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2.5 bg-lime-600 text-white rounded-xl hover:bg-lime-700 font-medium transition-colors"
              >
                {team ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
