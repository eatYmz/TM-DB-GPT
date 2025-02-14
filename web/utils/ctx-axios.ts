import axios from 'axios';
import { TokenManager } from './token';

const api = axios.create({
  baseURL: process.env.API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = TokenManager.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.defaults.timeout = 10000;

api.interceptors.response.use(
  response => response.data,
	err => Promise.reject(err)
);

export default api;