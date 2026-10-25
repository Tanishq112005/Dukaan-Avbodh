import apiClient from "./api";
import { useStore } from "../store/useStore";

/**
 * Valid event types supported by Dukaan backend (UserEvents/models.py).
 */
export const EVENT_TYPES = {
  VIEWED: "viewed",
  PURCHASED: "purchased",
  SUGGESTION_ACCEPTED: "suggestion_accepted",
  SUGGESTION_SKIPPED: "suggestion_skipped",
  SESSION_START: "session_start",
  ADD_TO_CART: "add_to_cart",
  REMOVE_FROM_CART: "remove_from_cart",
};

/**
 * Service for tracking user telemetry and events.
 * Interfaces with UserEvents/routes: /userEvents/*
 */
export const userEventService = {
  /**
   * Tracks a user interaction event.
   * Silently ignores if user is not authenticated yet.
   * @param {string} eventType - One of EVENT_TYPES
   * @param {number|null} [productId=null] - Product ID associated with event
   * @returns {Promise<Object|null>}
   */
  async trackEvent(eventType, productId = null) {
    const token = useStore.getState().token;
    if (!token) {
      // Guest users cannot persist to /userEvents/add due to auth_middleware requirement
      return null;
    }

    try {
      const payload = {
        event_type: eventType,
        product_id: productId ? Number(productId) : 0,
      };

      const res = await apiClient.post("/userEvents/add", payload);
      return res.data;
    } catch (err) {
      // Telemetry should never crash the user experience
      console.debug("[UserEvents] Telemetry track failed silently:", err?.message || err);
      return null;
    }
  },

  /**
   * Fetches the authenticated user's tracked events.
   * @returns {Promise<Array>}
   */
  async getUserEvents() {
    try {
      const res = await apiClient.get("/userEvents/get");
      return res.data.events || res.data || [];
    } catch (err) {
      console.warn("[UserEvents] Failed to fetch user events:", err);
      return [];
    }
  },

  /**
   * Merchant / admin: Fetches recent user events across all users.
   * @param {number} [limit=10]
   * @returns {Promise<Array>}
   */
  async getAllUserEvents(limit = 10) {
    try {
      const res = await apiClient.get(`/userEvents/allUserEvents?limit=${limit}`);
      return res.data.events || res.data || [];
    } catch (err) {
      console.warn("[UserEvents] Failed to fetch all user events:", err);
      return [];
    }
  },
};

export default userEventService;
