import axios from 'axios';

const API_BASE_URL = 'http://localhost:8090';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every request automatically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global 401 handler — clear token and redirect to login when token is expired/invalid (except on login endpoint itself)
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const isLoginReq = error.config?.url?.includes('/api/auth/login');
    if (status === 401 && !isLoginReq) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default client;
