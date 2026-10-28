import apiClient from "./api";

/**
 * Service to fetch real-time server health and subsystem diagnostics.
 */
export const healthService = {
  /**
   * Fetches full diagnostic health metrics from the backend.
   * Handles 503 (degraded/unhealthy) gracefully as valid response data.
   */
  async getServerHealth() {
    try {
      const response = await apiClient.get("/health", {
        params: { format: "json" },
        validateStatus: (status) => status < 600, // Treat 503 as payload-bearing response
      });
      return response.data;
    } catch (error) {
      console.error("[HealthService] Failed to fetch server health:", error);
      throw error;
    }
  },

  /**
   * Fast liveness probe.
   */
  async checkLiveness() {
    const response = await apiClient.get("/health/live");
    return response.data;
  },

  /**
   * Database & Redis readiness probe.
   */
  async checkReadiness() {
    const response = await apiClient.get("/health/ready", {
      validateStatus: (status) => status < 600,
    });
    return response.data;
  },
};

export default healthService;
