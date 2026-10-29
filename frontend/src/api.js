import axios from 'axios';

const defaultApiUrl = import.meta.env.DEV
  ? 'http://localhost:5000'
  : 'https://smart-agri-vnpj.onrender.com';

const apiBaseUrl = (import.meta.env.VITE_API_URL || defaultApiUrl)
  .trim()
  .replace(/\/+$/, '');

const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
});

export default api;
