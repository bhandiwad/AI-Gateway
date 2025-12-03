import { useState, useEffect } from 'react';
import { 
  Shield, 
  Plus, 
  Trash2, 
  Edit2, 
  Save, 
  X, 
  ChevronUp, 
  ChevronDown,
  Check,
  AlertTriangle,
  Settings,
  Eye,
  Filter
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const PROCESSOR_TYPES = [
  { id: 'pii_detector', name: 'PII Detector', desc: 'Detects and redacts personal information', phase: 'request' },
  { id: 'toxicity_filter', name: 'Toxicity Filter', desc: 'Blocks harmful or offensive content', phase: 'both' },
  { id: 'prompt_injection', name: 'Prompt Injection Guard', desc: 'Prevents prompt injection attacks', phase: 'request' },
  { id: 'jailbreak_detector', name: 'Jailbreak Detector', desc: 'Detects attempts to bypass AI safety', phase: 'request' },
  { id: 'financial_advice', name: 'Financial Advice Guard', desc: 'Flags investment/financial advice', phase: 'response' },
  { id: 'confidential_data', name: 'Confidential Data Filter', desc: 'Prevents disclosure of sensitive data', phase: 'response' },
  { id: 'rate_limiter', name: 'Rate Limiter', desc: 'Enforces request rate limits', phase: 'request' },
  { id: 'content_filter', name: 'Content Filter', desc: 'Custom keyword filtering', phase: 'both' },
  { id: 'output_validator', name: 'Output Validator', desc: 'Validates response format', phase: 'response' },
  { id: 'cost_guard', name: 'Cost Guard', desc: 'Limits token/cost per request', phase: 'request' }
];

export default function PolicyDesigner({ onProfileSelect }) {
  const { token, hasPermission } = useAuth();
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [editingProfile, setEditingProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProfile, setNewProfile] = useState({
    name: '',
    description: '',
    is_default: false
  });

  const canEdit = hasPermission('guardrails:edit');

  useEffect(() => {
    fetchProfiles();
  }, [token]);

  const fetchProfiles = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/providers/profiles/list', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfiles(response.data || []);
      if (response.data?.length > 0 && !selectedProfile) {
        setSelectedProfile(response.data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch profiles:', err);
      setError('Failed to load guardrail profiles');
    } finally {
      setLoading(false);
    }
  };

  const createProfile = async () => {
    if (!newProfile.name) {
      setError('Profile name is required');
      return;
    }

    try {
      setSaving(true);
      const response = await api.post('/admin/providers/profiles', {
        ...newProfile,
        request_processors: [],
        response_processors: []
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setProfiles([...profiles, response.data]);
      setSelectedProfile(response.data);
      setShowCreateModal(false);
      setNewProfile({ name: '', description: '', is_default: false });
    } catch (err) {
      console.error('Failed to create profile:', err);
      setError(err.response?.data?.detail || 'Failed to create profile');
    } finally {
      setSaving(false);
    }
  };

  const saveProfile = async () => {
    if (!editingProfile) return;

    try {
      setSaving(true);
      await api.put(`/admin/providers/profiles/${editingProfile.id}`, editingProfile, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setProfiles(profiles.map(p => p.id === editingProfile.id ? editingProfile : p));
      setSelectedProfile(editingProfile);
      setEditingProfile(null);
    } catch (err) {
      console.error('Failed to save profile:', err);
      setError(err.response?.data?.detail || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const deleteProfile = async (profileId) => {
    if (!confirm('Delete this profile? This cannot be undone.')) return;

    try {
      await api.delete(`/admin/providers/profiles/${profileId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const newProfiles = profiles.filter(p => p.id !== profileId);
      setProfiles(newProfiles);
      if (selectedProfile?.id === profileId) {
        setSelectedProfile(newProfiles[0] || null);
      }
    } catch (err) {
      console.error('Failed to delete profile:', err);
      setError('Failed to delete profile');
    }
  };

  const addProcessor = (phase, processorType) => {
    if (!editingProfile) return;

    const processor = PROCESSOR_TYPES.find(p => p.id === processorType);
    if (!processor) return;

    const newProcessor = {
      id: `${processorType}-${Date.now()}`,
      type: processorType,
      name: processor.name,
      enabled: true,
      config: {}
    };

    if (phase === 'request') {
      setEditingProfile({
        ...editingProfile,
        request_processors: [...(editingProfile.request_processors || []), newProcessor]
      });
    } else {
      setEditingProfile({
        ...editingProfile,
        response_processors: [...(editingProfile.response_processors || []), newProcessor]
      });
    }
  };

  const removeProcessor = (phase, processorId) => {
    if (!editingProfile) return;

    if (phase === 'request') {
      setEditingProfile({
        ...editingProfile,
        request_processors: editingProfile.request_processors.filter(p => p.id !== processorId)
      });
    } else {
      setEditingProfile({
        ...editingProfile,
        response_processors: editingProfile.response_processors.filter(p => p.id !== processorId)
      });
    }
  };

  const moveProcessor = (phase, index, direction) => {
    if (!editingProfile) return;

    const processors = phase === 'request' 
      ? [...(editingProfile.request_processors || [])]
      : [...(editingProfile.response_processors || [])];

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= processors.length) return;

    [processors[index], processors[newIndex]] = [processors[newIndex], processors[index]];

    if (phase === 'request') {
      setEditingProfile({ ...editingProfile, request_processors: processors });
    } else {
      setEditingProfile({ ...editingProfile, response_processors: processors });
    }
  };

  const toggleProcessor = (phase, processorId) => {
    if (!editingProfile) return;

    if (phase === 'request') {
      setEditingProfile({
        ...editingProfile,
        request_processors: editingProfile.request_processors.map(p => 
          p.id === processorId ? { ...p, enabled: !p.enabled } : p
        )
      });
    } else {
      setEditingProfile({
        ...editingProfile,
        response_processors: editingProfile.response_processors.map(p => 
          p.id === processorId ? { ...p, enabled: !p.enabled } : p
        )
      });
    }
  };

  const [openDropdown, setOpenDropdown] = useState(null);

  const renderProcessorList = (phase, processors) => {
    const availableProcessors = PROCESSOR_TYPES.filter(p => 
      p.phase === phase || p.phase === 'both'
    );

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            {phase === 'request' ? (
              <>
                <Filter size={16} className="text-blue-600" />
                Request Processors
              </>
            ) : (
              <>
                <Eye size={16} className="text-green-600" />
                Response Processors
              </>
            )}
          </h4>
          {editingProfile && canEdit && (
            <div className="relative">
              <button 
                onClick={() => setOpenDropdown(openDropdown === phase ? null : phase)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded flex items-center gap-1"
              >
                <Plus size={14} />
                Add
              </button>
              {openDropdown === phase && (
                <div className="absolute right-0 top-full mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                  {availableProcessors.map(processor => (
                    <button
                      key={processor.id}
                      onClick={() => {
                        addProcessor(phase, processor.id);
                        setOpenDropdown(null);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                    >
                      <div className="font-medium text-gray-900">{processor.name}</div>
                      <div className="text-xs text-gray-500">{processor.desc}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-2">
          {(processors || []).length === 0 ? (
            <div className="text-center py-6 text-gray-400 text-sm border border-dashed border-gray-200 rounded-lg">
              No processors configured
            </div>
          ) : (
            processors.map((processor, idx) => (
              <div
                key={processor.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  processor.enabled 
                    ? 'bg-white border-gray-200' 
                    : 'bg-gray-50 border-gray-100 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="flex flex-col gap-0.5">
                    {editingProfile && (
                      <>
                        <button
                          onClick={() => moveProcessor(phase, idx, 'up')}
                          disabled={idx === 0}
                          className="p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        >
                          <ChevronUp size={14} />
                        </button>
                        <button
                          onClick={() => moveProcessor(phase, idx, 'down')}
                          disabled={idx === processors.length - 1}
                          className="p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        >
                          <ChevronDown size={14} />
                        </button>
                      </>
                    )}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 text-sm">{processor.name}</div>
                    <div className="text-xs text-gray-500">
                      {PROCESSOR_TYPES.find(p => p.id === processor.type)?.desc || 'Custom processor'}
                    </div>
                  </div>
                </div>
                {editingProfile && canEdit && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleProcessor(phase, processor.id)}
                      className={`p-1 rounded ${
                        processor.enabled 
                          ? 'text-green-600 hover:bg-green-50' 
                          : 'text-gray-400 hover:bg-gray-100'
                      }`}
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={() => removeProcessor(phase, processor.id)}
                      className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-500" size={20} />
          <span className="text-red-700">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <X size={18} />
          </button>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Shield size={28} className="text-gray-700" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Guardrail Profiles</h2>
              <p className="text-sm text-gray-600">Configure request and response processor chains</p>
            </div>
          </div>
          {canEdit && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus size={16} />
              New Profile
            </button>
          )}
        </div>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-2xl font-bold text-gray-900">{profiles.length}</p>
            <p className="text-sm text-gray-500">Profiles</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-2xl font-bold text-green-600">{profiles.filter(p => p.is_active !== false).length}</p>
            <p className="text-sm text-gray-500">Active</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-2xl font-bold text-gray-900">
              {profiles.reduce((sum, p) => sum + (p.request_processors?.length || 0), 0)}
            </p>
            <p className="text-sm text-gray-500">Request Processors</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-2xl font-bold text-gray-900">
              {profiles.reduce((sum, p) => sum + (p.response_processors?.length || 0), 0)}
            </p>
            <p className="text-sm text-gray-500">Response Processors</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="p-4 border-b bg-gray-50">
            <h3 className="font-semibold text-gray-900">Profiles</h3>
          </div>
          <div className="divide-y">
            {profiles.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <Shield size={32} className="mx-auto mb-2 opacity-50" />
                <p>No profiles yet</p>
              </div>
            ) : (
              profiles.map(profile => (
                <div
                  key={profile.id}
                  onClick={() => {
                    setSelectedProfile(profile);
                    setEditingProfile(null);
                  }}
                  className={`p-4 cursor-pointer hover:bg-gray-50 ${
                    selectedProfile?.id === profile.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{profile.name}</div>
                      {profile.description && (
                        <div className="text-xs text-gray-500 mt-0.5">{profile.description}</div>
                      )}
                    </div>
                    {profile.is_default && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Default</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>{profile.request_processors?.length || 0} request</span>
                    <span>{profile.response_processors?.length || 0} response</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          {selectedProfile ? (
            <>
              <div className="p-4 border-b bg-gray-50 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedProfile.name}</h3>
                  {selectedProfile.description && (
                    <p className="text-sm text-gray-500">{selectedProfile.description}</p>
                  )}
                </div>
                {canEdit && (
                  <div className="flex items-center gap-2">
                    {editingProfile ? (
                      <>
                        <button
                          onClick={() => setEditingProfile(null)}
                          className="px-3 py-1.5 text-gray-600 bg-white border border-gray-300 rounded hover:bg-gray-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={saveProfile}
                          disabled={saving}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                        >
                          <Save size={14} />
                          {saving ? 'Saving...' : 'Save'}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => setEditingProfile({ ...selectedProfile })}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center gap-1"
                        >
                          <Edit2 size={14} />
                          Edit
                        </button>
                        <button
                          onClick={() => deleteProfile(selectedProfile.id)}
                          className="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="p-6 space-y-6">
                {renderProcessorList('request', 
                  editingProfile?.request_processors || selectedProfile.request_processors
                )}
                
                <div className="border-t pt-6">
                  {renderProcessorList('response', 
                    editingProfile?.response_processors || selectedProfile.response_processors
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-gray-400">
              <Settings size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">Select a profile to view details</p>
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Create Guardrail Profile</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newProfile.name}
                  onChange={(e) => setNewProfile({ ...newProfile, name: e.target.value })}
                  placeholder="e.g., Enterprise Compliance"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newProfile.description}
                  onChange={(e) => setNewProfile({ ...newProfile, description: e.target.value })}
                  placeholder="Describe this profile..."
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newProfile.is_default}
                  onChange={(e) => setNewProfile({ ...newProfile, is_default: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600"
                />
                <span className="text-sm text-gray-700">Set as default profile</span>
              </label>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={createProfile}
                disabled={saving || !newProfile.name}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Creating...' : 'Create Profile'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
