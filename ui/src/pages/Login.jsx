import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2, Shield } from 'lucide-react';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [ssoProvider, setSsoProvider] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [ssoLoading, setSsoLoading] = useState(false);
  const { login, loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const provider = searchParams.get('provider');
    
    if (code && state && provider) {
      handleSSOCallback(code, state, provider);
    }
  }, [searchParams]);

  const handleSSOCallback = async (code, state, provider) => {
    setSsoLoading(true);
    setError('');
    
    try {
      const redirectUri = `${window.location.origin}/login`;
      const response = await axios.get('/api/v1/admin/auth/sso/callback', {
        params: { code, state, redirect_uri: redirectUri, provider_name: provider }
      });
      
      loginWithToken(response.data.access_token, response.data.user);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'SSO authentication failed');
    } finally {
      setSsoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSSOLogin = async () => {
    if (!ssoProvider.trim()) {
      setError('Please enter your SSO provider name');
      return;
    }
    
    setSsoLoading(true);
    setError('');

    try {
      const redirectUri = `${window.location.origin}/login?provider=${ssoProvider}`;
      const response = await axios.post('/api/v1/admin/auth/sso/initiate', {
        provider_name: ssoProvider,
        redirect_uri: redirectUri
      });
      
      window.location.href = response.data.authorization_url;
    } catch (err) {
      setError(err.response?.data?.detail || 'SSO initialization failed. Provider may not be configured.');
      setSsoLoading(false);
    }
  };

  if (ssoLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4" size={48} />
          <p className="text-gray-600">Authenticating with SSO...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4 py-8">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-6 sm:p-8">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">AI Gateway</h1>
          <p className="text-gray-500 mt-2 text-sm sm:text-base">Sign in to your account</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 flex items-center justify-center gap-2 text-base font-medium min-h-[48px] transition-colors"
          >
            {loading && <Loader2 className="animate-spin" size={20} />}
            Sign In
          </button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or continue with SSO</span>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              SSO Provider Name
            </label>
            <input
              type="text"
              value={ssoProvider}
              onChange={(e) => setSsoProvider(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
              placeholder="e.g., okta, auth0, azure-ad"
            />
          </div>
          
          <button
            type="button"
            onClick={handleSSOLogin}
            disabled={ssoLoading}
            className="w-full py-3 px-4 bg-gray-800 text-white rounded-lg hover:bg-gray-900 active:bg-gray-950 disabled:opacity-50 flex items-center justify-center gap-2 text-base font-medium min-h-[48px] transition-colors"
          >
            <Shield size={20} />
            Sign in with SSO
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-gray-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-600 hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
