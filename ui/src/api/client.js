import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('tenant');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post('/admin/auth/register', data),
  login: (data) => api.post('/admin/auth/login', data),
  me: () => api.get('/admin/auth/me'),
};

export const tenantsApi = {
  list: (skip = 0, limit = 100) => api.get(`/admin/tenants?skip=${skip}&limit=${limit}`),
  get: (id) => api.get(`/admin/tenants/${id}`),
  update: (id, data) => api.put(`/admin/tenants/${id}`, data),
};

export const apiKeysApi = {
  list: () => api.get('/admin/api-keys'),
  create: (data) => api.post('/admin/api-keys', data),
  revoke: (id) => api.delete(`/admin/api-keys/${id}`),
};

export const usageApi = {
  summary: (days = 30) => api.get(`/admin/usage/summary?days=${days}`),
  dashboard: (days = 30) => api.get(`/admin/usage/dashboard?days=${days}`),
};

export const modelsApi = {
  list: () => api.get('/admin/models'),
};

export const chatApi = {
  complete: async (apiKey, model, messages, stream = false) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({ model, messages, stream }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    if (stream) {
      return response.body;
    }
    
    return response.json();
  },
};

export default api;
