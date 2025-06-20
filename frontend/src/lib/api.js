import axios from 'axios';
import { getAuthHeaders, isAuthenticated, updateToken } from './keycloak';

/**
 * API client configuration and utilities.
 *
 * This module provides a configured axios instance with authentication
 * support, request/response interceptors, and utility functions for
 * making API calls to the backend.
 */

// Get base URL from environment or default to localhost
const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
export const BASE_URL = `${API_BASE}/api/v1`;

/**
 * Create axios instance with default configuration.
 */
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add authentication headers.
 */
apiClient.interceptors.request.use(
  async (config) => {
    try {
      // Add authentication headers if user is authenticated
      if (isAuthenticated()) {
        // Ensure token is fresh (refresh if expires within 30 seconds)
        await updateToken(30);

        // Add auth headers
        const authHeaders = getAuthHeaders();
        config.headers = {
          ...config.headers,
          ...authHeaders,
        };
      }

      // Log request in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
          headers: config.headers,
          data: config.data,
        });
      }

      return config;
    } catch (error) {
      console.error('Request interceptor error:', error);
      return config;
    }
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle common errors and responses.
 */
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} ${response.config.url}`, {
        data: response.data,
      });
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle authentication errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        await updateToken(0);

        // Retry the original request with new token
        const authHeaders = getAuthHeaders();
        originalRequest.headers = {
          ...originalRequest.headers,
          ...authHeaders,
        };

        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);

        // Token refresh failed, redirect to login
        if (isAuthenticated()) {
          window.location.href = '/login';
        }

        return Promise.reject(error);
      }
    }

    // Log error in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`API Error: ${error.response?.status || 'Network'} ${error.config?.url}`, {
        message: error.message,
        response: error.response?.data,
      });
    }

    return Promise.reject(error);
  }
);

/**
 * Generic API request function with error handling.
 */
const apiRequest = async (config) => {
  try {
    const response = await apiClient(config);
    return {
      data: response.data,
      status: response.status,
      headers: response.headers,
    };
  } catch (error) {
    // Transform error to a consistent format
    const apiError = {
      message: error.message || 'An error occurred',
      status: error.response?.status || 0,
      data: error.response?.data || null,
      code: error.code || 'UNKNOWN_ERROR',
    };

    throw apiError;
  }
};

/**
 * GET request helper.
 */
export const get = async (url, params = {}, config = {}) => {
  return apiRequest({
    method: 'GET',
    url,
    params,
    ...config,
  });
};

/**
 * POST request helper.
 */
export const post = async (url, data = {}, config = {}) => {
  return apiRequest({
    method: 'POST',
    url,
    data,
    ...config,
  });
};

/**
 * PUT request helper.
 */
export const put = async (url, data = {}, config = {}) => {
  return apiRequest({
    method: 'PUT',
    url,
    data,
    ...config,
  });
};

/**
 * PATCH request helper.
 */
export const patch = async (url, data = {}, config = {}) => {
  return apiRequest({
    method: 'PATCH',
    url,
    data,
    ...config,
  });
};

/**
 * DELETE request helper.
 */
export const del = async (url, config = {}) => {
  return apiRequest({
    method: 'DELETE',
    url,
    ...config,
  });
};

/**
 * Upload file helper with progress tracking.
 */
export const uploadFile = async (url, file, onProgress = null, config = {}) => {
  const formData = new FormData();
  formData.append('file', file);

  return apiRequest({
    method: 'POST',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: onProgress ? (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress(percentCompleted);
    } : undefined,
    ...config,
  });
};

/**
 * Authentication API endpoints.
 */
export const authAPI = {
  /**
   * Get current user information.
   */
  getCurrentUser: () => get('/auth/me'),

  /**
   * Get user profile (works with or without auth).
   */
  getUserProfile: () => get('/auth/profile'),

  /**
   * Validate authentication token.
   */
  validateToken: () => post('/auth/validate-token'),

  /**
   * Get authentication configuration.
   */
  getAuthConfig: () => get('/auth/config'),

  /**
   * Check authentication service health.
   */
  getAuthHealth: () => get('/auth/health'),

  /**
   * Introspect token with Keycloak.
   */
  introspectToken: () => post('/auth/introspect'),

  /**
   * Get user info from token.
   */
  getUserInfoFromToken: () => get('/auth/user-info'),
};

/**
 * Visualizations API endpoints.
 */
export const visualizationsAPI = {
  /**
   * Get all visualizations for the current user.
   */
  getAll: (params = {}) => get('/visualizations/', params),

  /**
   * Get a specific visualization by ID.
   */
  getById: (id) => get(`/visualizations/${id}`),

  /**
   * Create a new visualization.
   */
  create: (data) => post('/visualizations/', data),

  /**
   * Update an existing visualization.
   */
  update: (id, data) => put(`/visualizations/${id}`, data),

  /**
   * Delete a visualization.
   */
  delete: (id) => del(`/visualizations/${id}`),

  /**
   * Generate a new visualization from prompt.
   */
  generate: (promptData) => post('/visualizations/generate', promptData),

  /**
   * Get visualization tags.
   */
  getTags: (id) => get(`/visualizations/${id}/tags`),

  /**
   * Update visualization tags.
   */
  updateTags: (id, tags) => put(`/visualizations/${id}/tags`, { tags }),
};

/**
 * History API endpoints.
 */
export const historyAPI = {
  /**
   * Get user's generation history.
   */
  getAll: (params = {}) => get('/history/', params),

  /**
   * Get specific history entry.
   */
  getById: (id) => get(`/history/${id}`),

  /**
   * Delete history entry.
   */
  delete: (id) => del(`/history/${id}`),

  /**
   * Clear all history.
   */
  clearAll: () => del('/history/'),
};

/**
 * Prompts API endpoints.
 */
export const promptsAPI = {
  /**
   * Get all prompts.
   */
  getAll: (params = {}) => get('/prompts/', params),

  /**
   * Get specific prompt by ID.
   */
  getById: (id) => get(`/prompts/${id}`),

  /**
   * Create a new prompt.
   */
  create: (data) => post('/prompts/', data),

  /**
   * Update an existing prompt.
   */
  update: (id, data) => put(`/prompts/${id}`, data),

  /**
   * Delete a prompt.
   */
  delete: (id) => del(`/prompts/${id}`),

  /**
   * Generate content from prompt.
   */
  generate: (promptData) => post('/prompts/generate', promptData),
};

/**
 * Admin API endpoints (requires admin privileges).
 */
export const adminAPI = {
  /**
   * Get system statistics.
   */
  getStats: () => get('/admin/stats'),

  /**
   * Get all users (admin only).
   */
  getUsers: (params = {}) => get('/admin/users', params),

  /**
   * Get user by ID (admin only).
   */
  getUserById: (id) => get(`/admin/users/${id}`),

  /**
   * Update user (admin only).
   */
  updateUser: (id, data) => put(`/admin/users/${id}`, data),

  /**
   * Delete user (admin only).
   */
  deleteUser: (id) => del(`/admin/users/${id}`),

  /**
   * Get system health.
   */
  getHealth: () => get('/admin/health'),

  /**
   * Get vector store status.
   */
  getVectorStoreStatus: () => get('/admin/vector-store/status'),

  /**
   * Rebuild vector store.
   */
  rebuildVectorStore: () => post('/admin/vector-store/rebuild'),
};

/**
 * RAG (Retrieval-Augmented Generation) API endpoints.
 */
export const ragAPI = {
  /**
   * Search for similar content.
   */
  search: (query, params = {}) => post('/rag/search', { query, ...params }),

  /**
   * Get recommendations based on content.
   */
  getRecommendations: (contentId, params = {}) => get(`/rag/recommendations/${contentId}`, params),

  /**
   * Add content to RAG system.
   */
  addContent: (content) => post('/rag/content', content),

  /**
   * Update content in RAG system.
   */
  updateContent: (id, content) => put(`/rag/content/${id}`, content),

  /**
   * Remove content from RAG system.
   */
  removeContent: (id) => del(`/rag/content/${id}`),
};

/**
 * File upload endpoints.
 */
export const uploadAPI = {
  /**
   * Upload file for processing.
   */
  uploadFile: (file, onProgress) => uploadFile('/upload/', file, onProgress),

  /**
   * Upload multiple files.
   */
  uploadFiles: async (files, onProgress) => {
    const uploads = files.map((file, index) => {
      const fileProgress = onProgress ? (progress) => {
        onProgress(index, progress);
      } : null;
      return uploadFile('/upload/', file, fileProgress);
    });

    return Promise.all(uploads);
  },
};

/**
 * Utility functions for API responses.
 */
export const apiUtils = {
  /**
   * Check if error is an authentication error.
   */
  isAuthError: (error) => error.status === 401,

  /**
   * Check if error is a forbidden error.
   */
  isForbiddenError: (error) => error.status === 403,

  /**
   * Check if error is a validation error.
   */
  isValidationError: (error) => error.status === 422,

  /**
   * Check if error is a server error.
   */
  isServerError: (error) => error.status >= 500,

  /**
   * Extract error message from API error.
   */
  getErrorMessage: (error) => {
    if (error.data?.detail) {
      return Array.isArray(error.data.detail)
        ? error.data.detail.map(err => err.msg || err.message).join(', ')
        : error.data.detail;
    }

    if (error.data?.message) {
      return error.data.message;
    }

    return error.message || 'An unexpected error occurred';
  },
};

// Export the axios instance for advanced usage
export { apiClient };
export default apiClient;
