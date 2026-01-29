import { X, Code, Server, Shield, Zap, Clock, ArrowRight } from 'lucide-react';

const BUILT_IN_ROUTES = {
  '/chat/completions': {
    path: '/chat/completions',
    method: 'POST',
    title: 'Chat Completions',
    description: 'Generate chat completions using OpenAI-compatible API format. Supports streaming, function calling, and multi-turn conversations.',
    requestExample: `{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}`,
    responseExample: `{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699000000,
  "model": "gpt-4o",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}`,
    features: [
      { icon: Zap, label: 'Streaming', desc: 'Real-time token streaming with SSE' },
      { icon: Shield, label: 'Guardrails', desc: 'Content filtering and safety checks' },
      { icon: Server, label: 'Load Balancing', desc: 'Automatic failover between providers' },
      { icon: Clock, label: 'Rate Limiting', desc: 'Per-user and per-key limits' },
    ],
    curlExample: `curl -X POST "{{BASE_URL}}/chat/completions" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`
  },
  '/embeddings': {
    path: '/embeddings',
    method: 'POST',
    title: 'Text Embeddings',
    description: 'Generate vector embeddings for text input. Useful for semantic search, clustering, and similarity comparisons.',
    requestExample: `{
  "model": "text-embedding-3-small",
  "input": "The quick brown fox jumps over the lazy dog"
}`,
    responseExample: `{
  "object": "list",
  "data": [{
    "object": "embedding",
    "index": 0,
    "embedding": [0.0023, -0.0091, 0.0152, ...]
  }],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 9,
    "total_tokens": 9
  }
}`,
    features: [
      { icon: Zap, label: 'Batch Processing', desc: 'Multiple inputs in single request' },
      { icon: Server, label: 'Multiple Providers', desc: 'OpenAI, Cohere, and more' },
    ],
    curlExample: `curl -X POST "{{BASE_URL}}/embeddings" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "text-embedding-3-small",
    "input": "Hello world"
  }'`
  },
  '/models': {
    path: '/models',
    method: 'GET',
    title: 'List Models',
    description: 'Retrieve a list of all available models from configured providers. Use this to discover which models you can use.',
    requestExample: `// No request body required
GET /models`,
    responseExample: `{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1699000000,
      "owned_by": "openai"
    },
    {
      "id": "claude-3-sonnet",
      "object": "model",
      "created": 1699000000,
      "owned_by": "anthropic"
    }
  ]
}`,
    features: [
      { icon: Server, label: 'Multi-Provider', desc: 'Models from all configured providers' },
    ],
    curlExample: `curl "{{BASE_URL}}/models" \\
  -H "Authorization: Bearer YOUR_API_KEY"`
  },
  '/completions': {
    path: '/completions',
    method: 'POST',
    title: 'Text Completions',
    description: 'Generate text completions (legacy API). For new applications, prefer /chat/completions.',
    requestExample: `{
  "model": "gpt-3.5-turbo-instruct",
  "prompt": "Once upon a time",
  "max_tokens": 100,
  "temperature": 0.7
}`,
    responseExample: `{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1699000000,
  "model": "gpt-3.5-turbo-instruct",
  "choices": [{
    "text": ", in a land far away...",
    "index": 0,
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 20,
    "total_tokens": 25
  }
}`,
    features: [
      { icon: Zap, label: 'Simple Format', desc: 'Single prompt, single response' },
    ],
    curlExample: `curl -X POST "{{BASE_URL}}/completions" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-3.5-turbo-instruct",
    "prompt": "Hello"
  }'`
  }
};

export default function BuiltInRouteDetailModal({ isOpen, onClose, routePath, baseUrl }) {
  if (!isOpen || !routePath) return null;

  const route = BUILT_IN_ROUTES[routePath];
  if (!route) return null;

  const curlWithUrl = route.curlExample.replace(/\{\{BASE_URL\}\}/g, baseUrl);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-600 to-blue-700">
          <div className="flex items-center gap-3 text-white">
            <div className={`px-3 py-1 rounded-lg font-mono text-sm font-bold ${
              route.method === 'GET' ? 'bg-green-500' : 'bg-blue-400'
            }`}>
              {route.method}
            </div>
            <div>
              <h2 className="text-xl font-bold">{route.title}</h2>
              <p className="text-blue-100 font-mono text-sm">{route.path}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div>
            <p className="text-gray-700">{route.description}</p>
          </div>

          {route.features && route.features.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Features</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {route.features.map((feature, idx) => (
                  <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                    <feature.icon size={20} className="text-blue-600 mb-2" />
                    <p className="font-medium text-gray-900 text-sm">{feature.label}</p>
                    <p className="text-xs text-gray-500">{feature.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Request Example</h3>
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-64">
                {route.requestExample}
              </pre>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Response Example</h3>
              <pre className="bg-gray-900 text-blue-400 p-4 rounded-lg text-xs overflow-x-auto max-h-64">
                {route.responseExample}
              </pre>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">cURL Example</h3>
            <pre className="bg-gray-900 text-yellow-400 p-4 rounded-lg text-xs overflow-x-auto">
              {curlWithUrl}
            </pre>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
