import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import Header from '../components/Header';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { 
  Search, 
  Filter, 
  GripVertical, 
  Save, 
  RefreshCw,
  Check,
  X,
  Zap,
  MessageSquare,
  Image,
  Code,
  Plus,
  Edit2,
  Trash2
} from 'lucide-react';

export default function Models() {
  const { token, hasPermission } = useAuth();
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProvider, setFilterProvider] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [hasChanges, setHasChanges] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [formData, setFormData] = useState({
    model_id: '',
    name: '',
    provider: 'custom',
    context_length: 128000,
    input_cost_per_1k: 0,
    output_cost_per_1k: 0,
    supports_streaming: true,
    supports_functions: false,
    supports_vision: false,
    api_base_url: '',
    api_key_name: '',
    is_enabled: true
  });
  const [formError, setFormError] = useState('');

  const canEdit = hasPermission('router:edit');

  useEffect(() => {
    loadModels();
  }, [token]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/models/settings', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setModels(response.data.models || []);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to load models:', error);
      const fallbackResponse = await api.get('/admin/models', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setModels(fallbackResponse.data.map((m, idx) => ({
        ...m,
        is_enabled: true,
        display_order: idx
      })));
    } finally {
      setLoading(false);
    }
  };

  const toggleModel = async (modelId) => {
    if (!canEdit) return;
    
    const model = models.find(m => m.id === modelId);
    const newEnabled = !model.is_enabled;
    
    setModels(prev => prev.map(m => 
      m.id === modelId ? { ...m, is_enabled: newEnabled } : m
    ));
    
    try {
      await api.put(`/admin/models/${modelId}/toggle?enabled=${newEnabled}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Failed to toggle model:', error);
      setModels(prev => prev.map(m => 
        m.id === modelId ? { ...m, is_enabled: !newEnabled } : m
      ));
    }
  };

  const handleDragEnd = (result) => {
    if (!result.destination || !canEdit) return;

    const items = Array.from(models);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    const reorderedModels = items.map((m, idx) => ({
      ...m,
      display_order: idx
    }));
    
    setModels(reorderedModels);
    setHasChanges(true);
  };

  const saveOrder = async () => {
    if (!canEdit) return;
    
    setSaving(true);
    try {
      const modelOrder = models.map(m => m.id);
      await api.post('/admin/models/reorder', { model_order: modelOrder }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save order:', error);
    } finally {
      setSaving(false);
    }
  };

  const resetForm = () => {
    setFormData({
      model_id: '',
      name: '',
      provider: 'custom',
      context_length: 128000,
      input_cost_per_1k: 0,
      output_cost_per_1k: 0,
      supports_streaming: true,
      supports_functions: false,
      supports_vision: false,
      api_base_url: '',
      api_key_name: '',
      is_enabled: true
    });
    setFormError('');
  };

  const openAddModal = () => {
    resetForm();
    setShowAddModal(true);
  };

  const openEditModal = (model) => {
    setEditingModel(model);
    setFormData({
      model_id: model.id,
      name: model.name || model.id,
      provider: model.provider || 'custom',
      context_length: model.context_length || 128000,
      input_cost_per_1k: model.input_cost_per_1k || 0,
      output_cost_per_1k: model.output_cost_per_1k || 0,
      supports_streaming: model.supports_streaming !== false,
      supports_functions: model.supports_functions || false,
      supports_vision: model.supports_vision || false,
      api_base_url: model.api_base_url || '',
      api_key_name: model.api_key_name || '',
      is_enabled: model.is_enabled !== false
    });
    setFormError('');
    setShowEditModal(true);
  };

  const handleSubmitAdd = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!formData.model_id || !formData.name) {
      setFormError('Model ID and Name are required');
      return;
    }

    try {
      await api.post('/admin/models/custom', formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowAddModal(false);
      loadModels();
    } catch (error) {
      setFormError(error.response?.data?.detail || 'Failed to create model');
    }
  };

  const handleSubmitEdit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!editingModel) return;

    try {
      if (editingModel.is_custom) {
        await api.put(`/admin/models/custom/${editingModel.id}`, {
          name: formData.name,
          provider: formData.provider,
          context_length: formData.context_length,
          input_cost_per_1k: formData.input_cost_per_1k,
          output_cost_per_1k: formData.output_cost_per_1k,
          supports_streaming: formData.supports_streaming,
          supports_functions: formData.supports_functions,
          supports_vision: formData.supports_vision,
          api_base_url: formData.api_base_url || null,
          api_key_name: formData.api_key_name || null,
          is_enabled: formData.is_enabled
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await api.put(`/admin/models/${editingModel.id}/toggle?enabled=${formData.is_enabled}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowEditModal(false);
      setEditingModel(null);
      loadModels();
    } catch (error) {
      setFormError(error.response?.data?.detail || 'Failed to update model');
    }
  };

  const handleDelete = async (model) => {
    if (!model.is_custom) return;
    
    if (!confirm(`Are you sure you want to delete "${model.name}"?`)) return;

    try {
      await api.delete(`/admin/models/custom/${model.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
    }
  };

  const providers = [...new Set(models.map(m => m.provider))];

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesProvider = filterProvider === 'all' || model.provider === filterProvider;
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'enabled' && model.is_enabled) ||
                         (filterStatus === 'disabled' && !model.is_enabled) ||
                         (filterStatus === 'custom' && model.is_custom);
    return matchesSearch && matchesProvider && matchesStatus;
  });

  const getProviderColor = (provider) => {
    const colors = {
      openai: 'bg-slate-100 text-slate-800 border-slate-300',
      anthropic: 'bg-slate-100 text-slate-800 border-slate-300',
      google: 'bg-slate-100 text-slate-800 border-slate-300',
      xai: 'bg-slate-100 text-slate-800 border-slate-300',
      meta: 'bg-slate-100 text-slate-800 border-slate-300',
      mistral: 'bg-slate-100 text-slate-800 border-slate-300',
      cohere: 'bg-slate-100 text-slate-800 border-slate-300',
      'aws-bedrock': 'bg-slate-100 text-slate-800 border-slate-300',
      'azure-openai': 'bg-slate-100 text-slate-800 border-slate-300',
      'local-vllm': 'bg-slate-100 text-slate-800 border-slate-300',
      mock: 'bg-gray-100 text-gray-600 border-gray-300',
      custom: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    };
    return colors[provider] || 'bg-slate-100 text-slate-800 border-slate-300';
  };

  const formatCost = (cost) => {
    if (!cost && cost !== 0) return 'N/A';
    return `₹${(cost * 83.5).toFixed(4)}`;
  };

  const ModelFormModal = ({ isEdit, onSubmit, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEdit ? 'Edit Model' : 'Add Custom Model'}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {isEdit && !editingModel?.is_custom 
              ? 'You can only toggle enabled status for built-in models' 
              : 'Configure the model properties'}
          </p>
        </div>
        
        <form onSubmit={onSubmit} className="p-6 space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {formError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model ID *</label>
              <input
                type="text"
                value={formData.model_id}
                onChange={(e) => setFormData({...formData, model_id: e.target.value})}
                disabled={isEdit}
                placeholder="e.g., my-custom-model"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Display Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                disabled={isEdit && !editingModel?.is_custom}
                placeholder="e.g., My Custom Model"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
          </div>

          {(!isEdit || editingModel?.is_custom) && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                  <select
                    value={formData.provider}
                    onChange={(e) => setFormData({...formData, provider: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="custom">Custom</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google</option>
                    <option value="xai">xAI</option>
                    <option value="meta">Meta</option>
                    <option value="mistral">Mistral</option>
                    <option value="cohere">Cohere</option>
                    <option value="aws-bedrock">AWS Bedrock</option>
                    <option value="azure-openai">Azure OpenAI</option>
                    <option value="local-vllm">Local vLLM</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Context Length</label>
                  <input
                    type="number"
                    value={formData.context_length}
                    onChange={(e) => setFormData({...formData, context_length: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Input Cost ($/1K tokens)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.input_cost_per_1k}
                    onChange={(e) => setFormData({...formData, input_cost_per_1k: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Output Cost ($/1K tokens)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.output_cost_per_1k}
                    onChange={(e) => setFormData({...formData, output_cost_per_1k: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Base URL (optional)</label>
                  <input
                    type="url"
                    value={formData.api_base_url}
                    onChange={(e) => setFormData({...formData, api_base_url: e.target.value})}
                    placeholder="https://api.example.com/v1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">API Key Name (optional)</label>
                  <input
                    type="text"
                    value={formData.api_key_name}
                    onChange={(e) => setFormData({...formData, api_key_name: e.target.value})}
                    placeholder="e.g., CUSTOM_API_KEY"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.supports_streaming}
                    onChange={(e) => setFormData({...formData, supports_streaming: e.target.checked})}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">Supports Streaming</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.supports_functions}
                    onChange={(e) => setFormData({...formData, supports_functions: e.target.checked})}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">Supports Functions</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.supports_vision}
                    onChange={(e) => setFormData({...formData, supports_vision: e.target.checked})}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-700">Supports Vision</span>
                </label>
              </div>
            </>
          )}

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.is_enabled}
              onChange={(e) => setFormData({...formData, is_enabled: e.target.checked})}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <span className="text-sm font-medium text-gray-700">Enabled</span>
          </label>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {isEdit ? 'Save Changes' : 'Add Model'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="Model Catalog" />
      
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search models..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex flex-wrap items-center gap-2">
            <Filter size={18} className="text-gray-400" />
            <select
              value={filterProvider}
              onChange={(e) => setFilterProvider(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Providers</option>
              {providers.map(provider => (
                <option key={provider} value={provider}>
                  {provider.charAt(0).toUpperCase() + provider.slice(1)}
                </option>
              ))}
            </select>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
              <option value="custom">Custom Only</option>
            </select>
            
            <button
              onClick={loadModels}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title="Refresh"
            >
              <RefreshCw size={18} className="text-gray-600" />
            </button>
            
            {canEdit && (
              <button
                onClick={openAddModal}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus size={18} />
                Add Model
              </button>
            )}
            
            {hasChanges && canEdit && (
              <button
                onClick={saveOrder}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                <Save size={18} />
                {saving ? 'Saving...' : 'Save Order'}
              </button>
            )}
          </div>
        </div>

        {canEdit && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
            <GripVertical className="inline mr-2" size={16} />
            Drag models to reorder. Click edit to modify model properties. Toggle switches to enable/disable.
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-500 mb-4">
              Showing {filteredModels.length} of {models.length} models
              {models.filter(m => m.is_enabled).length > 0 && (
                <span className="ml-2 text-green-600">
                  ({models.filter(m => m.is_enabled).length} enabled)
                </span>
              )}
              {models.filter(m => m.is_custom).length > 0 && (
                <span className="ml-2 text-emerald-600">
                  ({models.filter(m => m.is_custom).length} custom)
                </span>
              )}
            </p>
            
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="models" isDropDisabled={!canEdit}>
                {(provided) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="space-y-3"
                  >
                    {filteredModels.map((model, index) => (
                      <Draggable 
                        key={model.id} 
                        draggableId={model.id} 
                        index={index}
                        isDragDisabled={!canEdit}
                      >
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            className={`bg-white rounded-lg shadow border border-gray-200 p-4 ${
                              snapshot.isDragging ? 'shadow-lg ring-2 ring-blue-500' : ''
                            } ${!model.is_enabled ? 'opacity-60' : ''}`}
                          >
                            <div className="flex items-center gap-4">
                              {canEdit && (
                                <div {...provided.dragHandleProps} className="cursor-grab">
                                  <GripVertical className="text-gray-400" size={20} />
                                </div>
                              )}
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 mb-2">
                                  <h3 className="font-semibold text-gray-900 truncate">
                                    {model.name}
                                  </h3>
                                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getProviderColor(model.provider)}`}>
                                    {model.provider}
                                  </span>
                                  {model.is_custom && (
                                    <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                                      Custom
                                    </span>
                                  )}
                                </div>
                                
                                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                  <span className="flex items-center gap-1">
                                    <MessageSquare size={14} />
                                    {((model.context_length || 0) / 1000).toFixed(0)}K context
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Zap size={14} />
                                    Input: {formatCost(model.input_cost_per_1k)}/1K
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Zap size={14} />
                                    Output: {formatCost(model.output_cost_per_1k)}/1K
                                  </span>
                                  {model.supports_vision && (
                                    <span className="flex items-center gap-1 text-gray-600">
                                      <Image size={14} />
                                      Vision
                                    </span>
                                  )}
                                  {model.supports_functions && (
                                    <span className="flex items-center gap-1 text-gray-600">
                                      <Code size={14} />
                                      Functions
                                    </span>
                                  )}
                                </div>
                              </div>
                              
                              <div className="flex items-center gap-3">
                                {canEdit && (
                                  <>
                                    <button
                                      onClick={() => openEditModal(model)}
                                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                                      title="Edit model"
                                    >
                                      <Edit2 size={18} />
                                    </button>
                                    {model.is_custom && (
                                      <button
                                        onClick={() => handleDelete(model)}
                                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                                        title="Delete model"
                                      >
                                        <Trash2 size={18} />
                                      </button>
                                    )}
                                  </>
                                )}
                                
                                <span className={`text-sm font-medium ${model.is_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                                  {model.is_enabled ? 'Enabled' : 'Disabled'}
                                </span>
                                
                                {canEdit ? (
                                  <button
                                    onClick={() => toggleModel(model.id)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                      model.is_enabled ? 'bg-green-600' : 'bg-gray-300'
                                    }`}
                                  >
                                    <span
                                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                        model.is_enabled ? 'translate-x-6' : 'translate-x-1'
                                      }`}
                                    />
                                  </button>
                                ) : (
                                  model.is_enabled ? (
                                    <Check className="text-green-600" size={20} />
                                  ) : (
                                    <X className="text-gray-400" size={20} />
                                  )
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>

            {filteredModels.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500">No models found matching your criteria</p>
              </div>
            )}
          </>
        )}
      </div>

      {showAddModal && (
        <ModelFormModal 
          isEdit={false} 
          onSubmit={handleSubmitAdd} 
          onClose={() => setShowAddModal(false)} 
        />
      )}

      {showEditModal && (
        <ModelFormModal 
          isEdit={true} 
          onSubmit={handleSubmitEdit} 
          onClose={() => { setShowEditModal(false); setEditingModel(null); }} 
        />
      )}
    </div>
  );
}
