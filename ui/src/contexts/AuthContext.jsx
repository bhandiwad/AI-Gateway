import { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('tenant');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
      authApi.me()
        .then((response) => {
          setUser(response.data);
          localStorage.setItem('tenant', JSON.stringify(response.data));
        })
        .catch(() => {
          localStorage.removeItem('token');
          localStorage.removeItem('tenant');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const response = await authApi.login({ email, password });
    const { access_token, tenant } = response.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('tenant', JSON.stringify(tenant));
    setUser(tenant);
    return tenant;
  };

  const loginWithToken = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('tenant', JSON.stringify(userData));
    setUser(userData);
  };

  const register = async (name, email, password) => {
    const response = await authApi.register({ name, email, password });
    const { access_token, tenant } = response.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('tenant', JSON.stringify(tenant));
    setUser(tenant);
    return tenant;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('tenant');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithToken, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
