import axios from "axios";
import { useStore } from "../store/useStore.js";

const API_BASE_URL = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://localhost:8000";

/**
 * Centralized Axios instance configured for Dukaan backend APIs.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor: Attach JWT token if available
apiClient.interceptors.request.use(
  (config) => {
    // Read token from Zustand store state
    const token = useStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Centralized error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;
    const detail = error.response?.data?.detail || error.message || "An unexpected error occurred.";

    if (status === 401) {
      console.warn("[API] Unauthorized (401) - token may be expired or invalid.");
      // If needed, we can trigger logout here if token is explicitly invalid
      // useStore.getState().logout();
    }

    return Promise.reject({
      status,
      message: typeof detail === "string" ? detail : JSON.stringify(detail),
      originalError: error,
    });
  }
);

export default apiClient;
