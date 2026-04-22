import axios from 'axios';
import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create base instance
const apiClient = axios.create({
  baseURL: API_URL,
});

// Intercept requests to add the auth token dynamically
apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export const uploadInvoice = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const saveInvoice = async (data: any) => {
  const response = await apiClient.post('/save', { data });
  return response.data;
};

export const getInvoices = async () => {
  const response = await apiClient.get('/invoices');
  return response.data;
};

export const getInvoiceById = async (id: string) => {
  const response = await apiClient.get(`/invoices/${id}`);
  return response.data;
};

export const deleteInvoices = async (invoiceIds: string[]) => {
  const response = await apiClient.post('/invoices/delete', { invoice_ids: invoiceIds });
  return response.data;
};

export const getUsers = async () => {
  const response = await apiClient.get('/users');
  return response.data;
};

export const createUser = async (email: string, password: string, role: string) => {
  const response = await apiClient.post('/users', { email, password, role });
  return response.data;
};

export const deleteUser = async (userId: string) => {
  const response = await apiClient.delete(`/users/${userId}`);
  return response.data;
};

export const getMe = async () => {
  const response = await apiClient.get('/me');
  return response.data;
};

export const getStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};
