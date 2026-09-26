import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api/v1` : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('healthmate_access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle token refresh or unauthorized
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('healthmate_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
          const { access_token, refresh_token: newRefreshToken } = res.data;
          localStorage.setItem('healthmate_access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('healthmate_refresh_token', newRefreshToken);
          }
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('healthmate_access_token');
          localStorage.removeItem('healthmate_refresh_token');
          localStorage.removeItem('healthmate_user');
          window.location.href = '/login';
        }
      } else {
        localStorage.removeItem('healthmate_access_token');
        localStorage.removeItem('healthmate_user');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
