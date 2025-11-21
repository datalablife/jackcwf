import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// Create axios instance with default config
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: Add auth token
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor: Handle errors and token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // Handle 401 Unauthorized - try to refresh token
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        try {
          // Try to refresh token
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {});
          const newToken = refreshResponse.data.token;
          localStorage.setItem('auth_token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Token refresh failed, logout user
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      // Handle 502/503 - retry with exponential backoff
      if ([502, 503].includes(error.response?.status)) {
        const retryCount = originalRequest._retryCount || 0;
        if (retryCount < 3) {
          originalRequest._retryCount = retryCount + 1;
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
          await new Promise((resolve) => setTimeout(resolve, delay));
          return client(originalRequest);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

const apiClient = createApiClient();

// Generic request wrapper
const request = async <T = unknown>(
  method: string,
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<ApiResponse<T>> => {
  try {
    const response = await apiClient({
      method,
      url,
      data,
      ...config,
    });
    return {
      data: response.data,
      metadata: {
        requestId: response.headers['x-request-id'],
        timestamp: new Date(),
      },
    };
  } catch (error) {
    const axiosError = error as any;
    return {
      error: {
        code: axiosError.response?.data?.code || 'UNKNOWN_ERROR',
        message: axiosError.response?.data?.message || axiosError.message,
        details: axiosError.response?.data?.details,
      },
    };
  }
};

// Conversation API
export const conversationApi = {
  getConversations: () =>
    request('GET', '/conversations'),

  createConversation: (data: { title: string }) =>
    request('POST', '/conversations', data),

  getConversation: (id: number) =>
    request('GET', `/conversations/${id}`),

  updateConversation: (id: number, data: { title?: string; metadata?: unknown }) =>
    request('PATCH', `/conversations/${id}`, data),

  deleteConversation: (id: number) =>
    request('DELETE', `/conversations/${id}`),

  generateTitle: (conversationId: string, content: string) =>
    request('POST', `/conversations/${conversationId}/generate-title`, { content }),
};

// Thread API (New endpoints for Epic 4)
export const threadApi = {
  createThread: (data: { title?: string; metadata?: unknown }) =>
    request('POST', '/threads', data),

  getThreadState: (threadId: string, query?: { include_messages?: boolean; message_limit?: number; include_tools?: boolean; use_cache?: boolean }) =>
    request('GET', `/threads/${threadId}/state`, undefined, { params: query }),

  submitToolResult: (threadId: string, data: { tool_id: string; tool_name: string; result: unknown; result_data?: unknown; execution_time_ms?: number }) =>
    request('POST', `/threads/${threadId}/tool-result`, data),
};

// Message API
export const messageApi = {
  getMessages: (conversationId: number, params?: { limit?: number; offset?: number }) =>
    request('GET', `/conversations/${conversationId}/messages`, undefined, { params }),

  getMessage: (messageId: number, query?: { include_tools?: boolean; include_metadata?: boolean }) =>
    request('GET', `/messages/${messageId}`, undefined, { params: query }),

  createMessage: (conversationId: number, data: { content: string; role?: string }) =>
    request('POST', `/conversations/${conversationId}/messages`, data),
};

// Document API
export const documentApi = {
  searchDocuments: (query: string, limit?: number) =>
    request('GET', '/documents/search', undefined, { params: { query, limit } }),

  uploadDocument: (file: File, metadata?: unknown) => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) formData.append('metadata', JSON.stringify(metadata));
    return request('POST', '/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  deleteDocument: (documentId: number) =>
    request('DELETE', `/documents/${documentId}`),
};

// Chat streaming API
export const streamingApi = {
  streamChat: (conversationId: number, message: string, query?: { include_state?: boolean; include_tools?: boolean; include_metadata?: boolean }) => {
    const url = `/conversations/${conversationId}/stream`;
    const params = new URLSearchParams();
    if (query?.include_state) params.append('include_state', 'true');
    if (query?.include_tools) params.append('include_tools', 'true');
    if (query?.include_metadata) params.append('include_metadata', 'true');

    return fetch(
      `${API_BASE_URL}${url}?${params.toString()}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token') || ''}`,
        },
        body: JSON.stringify({ content: message }),
      }
    );
  },
};

// Health check API
export const healthApi = {
  checkHealth: () => request('GET', '/health'),
};

export default apiClient;
