import { useState, useEffect } from 'react';
import { modelsApi, apiKeysApi } from '../api/client';
import Header from '../components/Header';
import PlaygroundChat from '../components/Playground';
import { Key, AlertCircle } from 'lucide-react';

export default function PlaygroundPage() {
  const [models, setModels] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [selectedKey, setSelectedKey] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [modelsRes, keysRes] = await Promise.all([
        modelsApi.list(),
        apiKeysApi.list()
      ]);
      setModels(modelsRes.data);
      setApiKeys(keysRes.data);
      
      const activeKey = keysRes.data.find(k => k.is_active);
      if (activeKey) {
        const storedKey = localStorage.getItem(`apikey_${activeKey.id}`);
        if (storedKey) {
          setSelectedKey(storedKey);
        }
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const activeKeys = apiKeys.filter(k => k.is_active);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <Header title="API Playground" />
      
      <div className="flex-1 overflow-hidden p-6 bg-gray-50">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {activeKeys.length === 0 ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <AlertCircle className="mx-auto text-amber-500 mb-4" size={48} />
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">No API Keys Found</h3>
                  <p className="text-gray-500 mb-4">Create an API key to use the playground</p>
                  <a
                    href="/api-keys"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Key size={18} />
                    Create API Key
                  </a>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Key size={18} className="text-gray-400" />
                    <input
                      type="password"
                      value={selectedKey}
                      onChange={(e) => setSelectedKey(e.target.value)}
                      placeholder="Enter or paste your API key"
                      className="w-80 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  {!selectedKey && (
                    <p className="text-sm text-amber-600">
                      Enter your API key (from the API Keys page) to start testing
                    </p>
                  )}
                </div>
                
                <div className="flex-1 min-h-0">
                  <PlaygroundChat models={models} apiKey={selectedKey} />
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
