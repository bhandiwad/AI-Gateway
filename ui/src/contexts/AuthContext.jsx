import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/client';

const AuthContext = createContext(null);

export const PERMISSIONS = {
  API_KEYS_VIEW: 'api_keys:view',
  API_KEYS_CREATE: 'api_keys:create',
  API_KEYS_REVOKE: 'api_keys:revoke',
  BILLING_VIEW: 'billing:view',
  BILLING_EXPORT: 'billing:export',
  BILLING_INVOICE: 'billing:invoice',
  AUDIT_VIEW: 'audit:view',
  AUDIT_EXPORT: 'audit:export',
  USERS_VIEW: 'users:view',
  USERS_CREATE: 'users:create',
  USERS_EDIT: 'users:edit',
  USERS_DELETE: 'users:delete',
  GUARDRAILS_VIEW: 'guardrails:view',
  GUARDRAILS_EDIT: 'guardrails:edit',
  GUARDRAILS_TEST: 'guardrails:test',
  ROUTER_VIEW: 'router:view',
  ROUTER_EDIT: 'router:edit',
  GATEWAY_USE: 'gateway:use',
  DASHBOARD_VIEW: 'dashboard:view',
  SETTINGS_VIEW: 'settings:view',
  SETTINGS_EDIT: 'settings:edit',
};

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

  const hasPermission = useCallback((permission) => {
    if (!user) return false;
    if (!user.permissions) {
      if (user.role === 'admin') return true;
      if (user.role === 'manager') {
        const managerPerms = [
          PERMISSIONS.API_KEYS_VIEW, PERMISSIONS.API_KEYS_CREATE,
          PERMISSIONS.BILLING_VIEW, PERMISSIONS.BILLING_EXPORT,
          PERMISSIONS.AUDIT_VIEW, PERMISSIONS.USERS_VIEW,
          PERMISSIONS.USERS_CREATE, PERMISSIONS.USERS_EDIT,
          PERMISSIONS.GUARDRAILS_VIEW, PERMISSIONS.GUARDRAILS_TEST,
          PERMISSIONS.ROUTER_VIEW, PERMISSIONS.GATEWAY_USE,
          PERMISSIONS.DASHBOARD_VIEW, PERMISSIONS.SETTINGS_VIEW,
        ];
        return managerPerms.includes(permission);
      }
      if (user.role === 'user') {
        const userPerms = [PERMISSIONS.GATEWAY_USE, PERMISSIONS.DASHBOARD_VIEW, PERMISSIONS.API_KEYS_VIEW];
        return userPerms.includes(permission);
      }
      if (user.role === 'viewer') {
        const viewerPerms = [
          PERMISSIONS.DASHBOARD_VIEW, PERMISSIONS.BILLING_VIEW,
          PERMISSIONS.AUDIT_VIEW, PERMISSIONS.GUARDRAILS_VIEW,
          PERMISSIONS.ROUTER_VIEW,
        ];
        return viewerPerms.includes(permission);
      }
      return false;
    }
    return user.permissions.includes(permission);
  }, [user]);

  const hasAnyPermission = useCallback((permissions) => {
    return permissions.some(p => hasPermission(p));
  }, [hasPermission]);

  const hasAllPermissions = useCallback((permissions) => {
    return permissions.every(p => hasPermission(p));
  }, [hasPermission]);

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

  const token = localStorage.getItem('token');

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      token,
      login, 
      loginWithToken, 
      register, 
      logout,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      role: user?.role || null,
      permissions: user?.permissions || []
    }}>
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
