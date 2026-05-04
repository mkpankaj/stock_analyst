import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
};

export const configAPI = {
  getConfig: () => api.get('/config'),
  saveConfig: (stock_universe, duration_days) =>
    api.post('/config', { stock_universe, duration_days }),
};

export const analysisAPI = {
  trigger: () => api.post('/analysis/trigger'),
  getStatus: () => api.get('/analysis/status'),
  getLatest: () => api.get('/analysis/latest'),
  getByDate: (date) => api.get(`/analysis/${date}`),
  getDates: () => api.get('/analysis/dates'),
};

export const stockAPI = {
  getChart: (ticker, duration_days = 120) =>
    api.get(`/stock/${ticker}`, { params: { duration_days } }),
  getNews: (ticker) => api.get(`/stock/${ticker}/news`),
};

export default api;
