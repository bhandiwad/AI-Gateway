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
  Code
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

  const providers = [...new Set(models.map(m => m.provider))];

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesProvider = filterProvider === 'all' || model.provider === filterProvider;
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'enabled' && model.is_enabled) ||
                         (filterStatus === 'disabled' && !model.is_enabled);
    return matchesSearch && matchesProvider && matchesStatus;
  });

  const getProviderColor = (provider) => {
    const colors = {
      openai: 'bg-green-100 text-green-800 border-green-200',
      anthropic: 'bg-orange-100 text-orange-800 border-orange-200',
      google: 'bg-blue-100 text-blue-800 border-blue-200',
      mock: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return colors[provider] || 'bg-purple-100 text-purple-800 border-purple-200';
  };

  const formatCost = (cost) => {
    if (!cost && cost !== 0) return 'N/A';
    return `₹${(cost * 83).toFixed(4)}`;
  };

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
            </select>
            
            <button
              onClick={loadModels}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title="Refresh"
            >
              <RefreshCw size={18} className="text-gray-600" />
            </button>
            
            {hasChanges && canEdit && (
              <button
                onClick={saveOrder}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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
            Drag models to reorder. Toggle switches to enable/disable models for your organization.
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
                            className={`bg-white rounded-lg shadow p-4 ${
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
                                </div>
                                
                                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                  <span className="flex items-center gap-1">
                                    <MessageSquare size={14} />
                                    {(model.context_length / 1000).toFixed(0)}K context
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
                                    <span className="flex items-center gap-1 text-purple-600">
                                      <Image size={14} />
                                      Vision
                                    </span>
                                  )}
                                  {model.supports_functions && (
                                    <span className="flex items-center gap-1 text-blue-600">
                                      <Code size={14} />
                                      Functions
                                    </span>
                                  )}
                                </div>
                              </div>
                              
                              <div className="flex items-center gap-3">
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
    </div>
  );
}
