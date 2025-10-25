import axios from 'axios';

// Create axios instance for Analytics Service (separate microservice)
const analyticsAxios = axios.create({
  baseURL: process.env.REACT_APP_ANALYTICS_URL || 'http://localhost:8002',
});

// Request interceptor to add auth token
analyticsAxios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
analyticsAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to login
      localStorage.removeItem('accessToken');
      localStorage.removeItem('user');
      localStorage.removeItem('fhirClient');
      
      // Only redirect if not already on login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default analyticsAxios;

