import apiClient from "./api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Service for interacting with user and merchant AI agents.
 * Interfaces with agents.user.routes, routes.chat_routes, routes.merchant_routes, and Negotiation/routes.
 */
export const agentService = {
  /**
   * Sends a user message to the conversational shopping agent (Standard JSON).
   * @param {Object} payload
   * @param {number} payload.userId
   * @param {string} payload.threadId
   * @param {string} payload.text
   * @param {Array} [payload.cart=[]]
   * @returns {Promise<Object>}
   */
  async sendUserMessage({ userId, threadId, text, cart = [] }) {
    const res = await apiClient.post("/chat/message", {
      user_id: Number(userId),
      thread_id: String(threadId),
      text: String(text),
      cart,
    });
    return res.data;
  },

  /**
   * Sends a proactive or reactive trigger event to the user agent.
   * @param {Object} payload
   * @param {number} payload.userId
   * @param {string} payload.threadId
   * @param {string} payload.event - E.g. "payment_completed", "viewed_checkout", "combo_declined"
   * @param {Array} [payload.cart=[]]
   * @returns {Promise<Object>}
   */
  async sendUserEvent({ userId, threadId, event, cart = [] }) {
    const res = await apiClient.post("/chat/event", {
      user_id: Number(userId),
      thread_id: String(threadId),
      event: String(event),
      cart,
    });
    return res.data;
  },

  /**
   * Streams chat responses via Server-Sent Events (SSE).
   * @param {Object} payload
   * @param {number} payload.userId
   * @param {string} payload.threadId
   * @param {string} payload.text
   * @param {Array} [payload.cart=[]]
   * @param {Function} callbacks.onToken - Called for streaming text tokens
   * @param {Function} callbacks.onEvent - Called for execution events
   * @param {Function} callbacks.onComplete - Called with the final structured JSON payload
   * @param {Function} callbacks.onError - Called on error
   */
  async streamUserMessage(
    { userId, threadId, text, cart = [] },
    { onToken, onEvent, onComplete, onError } = {}
  ) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/message/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          user_id: Number(userId),
          thread_id: String(threadId),
          text: String(text),
          cart,
        }),
      });

      if (!response.ok) {
        throw new Error(`SSE streaming failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep the trailing incomplete event

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const rawData = trimmed.replace(/^data:\s*/, "");
          if (rawData === "[DONE]") {
            continue;
          }

          try {
            const parsed = JSON.parse(rawData);
            if (parsed.event === "token" && onToken) {
              onToken(parsed.token || parsed.content || "");
            } else if (parsed.event === "complete" && onComplete) {
              onComplete(parsed.payload || parsed);
            } else if (onEvent) {
              onEvent(parsed);
            }
          } catch {
            // Raw text fallback
            if (onToken) onToken(rawData);
          }
        }
      }
    } catch (err) {
      if (onError) onError(err);
      throw err;
    }
  },

  /**
   * Merchant Agent: Asks merchant assistant for store analytics and recommendations.
   * @param {Object} payload
   * @param {string} payload.text
   * @param {string} [payload.threadId]
   * @returns {Promise<Object>}
   */
  async sendMerchantMessage({ text, threadId = null }) {
    const res = await apiClient.post("/merchant/chat", {
      text,
      thread_id: threadId,
    });
    return res.data;
  },

  /**
   * Negotiation: Computes maximum possible discount percentage without breaching merchant margin.
   * @param {Array} items - List of cart or product items
   * @returns {Promise<Object>}
   */
  async getNegotiationMaxDiscount(items) {
    const res = await apiClient.post("/negotiation/max-discount", { items });
    return res.data;
  },

  /**
   * Negotiation: Computes next counter-offer discount percentage.
   * @param {Object} payload
   * @returns {Promise<Object>}
   */
  async getNegotiationNextDiscount(payload) {
    const res = await apiClient.post("/negotiation/next-discount", payload);
    return res.data;
  },
};

export default agentService;
