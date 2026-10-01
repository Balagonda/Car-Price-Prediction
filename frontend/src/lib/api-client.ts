/**
 * AutoWorth AI — Axios API Client
 *
 * Centralized HTTP client with:
 * - Base URL from environment
 * - JWT Authorization header injection
 * - Automatic token refresh on 401
 * - Standardized error handling
 */

import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" ? "" : "http://127.0.0.1:8000");

// ──────────────────────────────────────────────
// Axios Instance
// ──────────────────────────────────────────────
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30_000,
  withCredentials: true, // Send cookies (refresh token)
});

// ──────────────────────────────────────────────
// Request Interceptor — Attach Access Token
// ──────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// ──────────────────────────────────────────────
// Response Interceptor — Handle 401 & Errors
// ──────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Token expired — attempt silent refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newToken = (refreshResponse.data as { access_token: string })
          .access_token;
        localStorage.setItem("access_token", newToken);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch {
        // Refresh failed — clear auth state and redirect to login
        localStorage.removeItem("access_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

// ──────────────────────────────────────────────
// Typed API Error
// ──────────────────────────────────────────────
export interface APIError {
  success: false;
  message: string;
  error_code?: string;
  errors?: Array<{ field: string; message: string }>;
}

export function getAPIError(error: unknown): APIError {
  if (axios.isAxiosError(error) && error.response?.data) {
    const data = error.response.data;
    if (data.detail && typeof data.detail === 'object') {
      return data.detail as APIError;
    }
    if (data.detail && typeof data.detail === 'string') {
      return { success: false, message: data.detail };
    }
    return data as APIError;
  }
  return {
    success: false,
    message: error instanceof Error ? error.message : "An unexpected error occurred. Please try again.",
  };
}
