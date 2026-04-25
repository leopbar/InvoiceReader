import axios from 'axios';
import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api';

export interface Invoice {
  supplier: any;
  invoice_info: any;
  bill_to: any;
  ship_to: any;
  line_items: any[];
  totals: any;
  notes?: string;
  metadata?: any;
}

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

export const uploadInvoiceStreaming = async (
  file: File,
  onStep: (step: string, detail: string) => void,
  onResult: (result: any) => void,
  onError: (message: string) => void
): Promise<void> => {
  // Get auth token manually since we're using fetch, not axios
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/upload/stream`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    onError(`Upload failed (${response.status}): ${errorText}`);
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? ''; // Keep the last incomplete line in the buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const payload = JSON.parse(line.slice(6));
          if (payload.type === 'progress') {
            onStep(payload.step, payload.detail ?? '');
          } else if (payload.type === 'result') {
            onResult(payload.data);
          } else if (payload.type === 'error') {
            onError(payload.message ?? 'Unknown error');
          }
        } catch {
          // Ignore malformed SSE lines
        }
      }
    }
  }
};

export const saveInvoice = async (data: Invoice) => {
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
