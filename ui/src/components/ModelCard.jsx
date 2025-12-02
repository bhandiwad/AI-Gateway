import { Cpu, Zap, Eye, MessageSquare } from 'lucide-react';

const providerColors = {
  openai: 'bg-green-100 text-green-800',
  anthropic: 'bg-orange-100 text-orange-800',
  azure: 'bg-blue-100 text-blue-800',
  default: 'bg-gray-100 text-gray-800',
};

export default function ModelCard({ model }) {
  const providerClass = providerColors[model.provider] || providerColors.default;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{model.name}</h3>
          <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-1 ${providerClass}`}>
            {model.provider}
          </span>
        </div>
        <Cpu className="text-gray-400" size={24} />
      </div>

      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Context Length</span>
          <span className="font-medium">{(model.context_length / 1000).toFixed(0)}K tokens</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Input Cost</span>
          <span className="font-medium">${(model.input_cost_per_token * 1000000).toFixed(2)} / 1M</span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Output Cost</span>
          <span className="font-medium">${(model.output_cost_per_token * 1000000).toFixed(2)} / 1M</span>
        </div>
      </div>

      <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
        {model.supports_streaming && (
          <span className="flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
            <Zap size={12} />
            Streaming
          </span>
        )}
        {model.supports_vision && (
          <span className="flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">
            <Eye size={12} />
            Vision
          </span>
        )}
        {model.supports_functions && (
          <span className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs rounded">
            <MessageSquare size={12} />
            Functions
          </span>
        )}
      </div>
    </div>
  );
}
