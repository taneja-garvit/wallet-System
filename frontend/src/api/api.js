import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Generate UUID for idempotency keys
export const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Auth APIs
export const signup = async (name, email, password) => {
  const response = await api.post('/auth/signup', { name, email, password });
  return response.data;
};

export const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

// Wallet APIs (Single currency: INR)
export const getWallet = async () => {
  const response = await api.get('/wallet');
  return response.data;
};

export const updateWalletName = async (name) => {
  const response = await api.patch('/wallet/name', { name });
  return response.data;
};

// Transaction APIs (Single currency: INR)
export const transferMoney = async (receiverUserId, amount) => {
  const idempotencyKey = generateUUID(); // Auto-generate UUID!
  const response = await api.post(
    '/transactions/transfer',
    { 
      receiver_user_id: receiverUserId,
      amount 
    },
    { headers: { 'Idempotency-Key': idempotencyKey } }
  );
  return response.data;
};

export const getTransactions = async (limit = 20, cursor = null) => {
  const params = { limit };
  if (cursor) params.cursor = cursor;
  const response = await api.get('/transactions', { params });
  return response.data;
};

export default api;
