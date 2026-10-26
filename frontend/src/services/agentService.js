import apiClient from "./api.js";

const API_BASE_URL = (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) || "http://localhost:8000";

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
   * Streams chat responses in real-time via Server-Sent Events (SSE).
   * Connects to /chat/message/stream endpoint.
   * @param {Object} payload
   * @param {number} payload.userId
   * @param {string} payload.threadId
   * @param {string} payload.text
   * @param {Array} [payload.cart=[]]
   * @param {Object} callbacks
   * @param {Function} [callbacks.onToken] - Called for streaming word/character tokens
   * @param {Function} [callbacks.onNodeUpdate] - Called for graph progress nodes (director, negotiation, etc.)
   * @param {Function} [callbacks.onCard] - Called for real-time Generative UI cards
   * @param {Function} [callbacks.onComplete] - Called with the final structured JSON payload
   * @param {Function} [callbacks.onError] - Called on network/stream errors
   */
  async streamUserMessage(
    { userId, threadId, text, cart = [] },
    { onToken, onNodeUpdate, onCard, onComplete, onError } = {}
  ) {
    try {
      const headers = {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      };

      try {
        const stored = localStorage.getItem("dukaan-store");
        if (stored) {
          const parsedStored = JSON.parse(stored);
          const token = parsedStored?.state?.token;
          if (token) {
            headers["Authorization"] = `Bearer ${token}`;
          }
        }
      } catch {
        // Ignore localStorage retrieval issues
      }

      const response = await fetch(`${API_BASE_URL}/chat/message/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_id: Number(userId),
          thread_id: String(threadId),
          text: String(text),
          cart,
        }),
      });

      if (!response.ok) {
        throw new Error(`SSE streaming request failed with HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream not supported on response body.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // preserve incomplete trailing line

        for (const rawLine of lines) {
          const line = rawLine.trim();
          if (!line || !line.startsWith("data:")) continue;

          const rawData = line.replace(/^data:\s*/, "").trim();
          if (rawData === "[DONE]") {
            continue;
          }

          try {
            const parsed = JSON.parse(rawData);

            // 1. Streaming text tokens
            if (parsed.type === "token" || parsed.event === "token") {
              if (onToken) {
                onToken(parsed.content || parsed.token || "");
              }
            }
            // 2. LangGraph node lifecycle updates
            else if (parsed.type === "node_update" || parsed.event === "node_update") {
              if (onNodeUpdate) {
                onNodeUpdate(parsed.node, parsed);
              }
            }
            // 3. Generative UI cards streamed from tool execution
            else if (parsed.type === "card" || parsed.type === "cards") {
              if (onCard) {
                onCard(parsed.card || parsed.cards);
              }
            }
            // 4. Final structured chat reply payload
            else if (
              parsed.type === "chat_reply" ||
              parsed.event === "complete" ||
              parsed.type === "proactive_suggestion"
            ) {
              if (onComplete) {
                onComplete(parsed);
              }
            }
            // 5. Server-reported error payload
            else if (parsed.error) {
              if (onComplete) {
                onComplete({
                  type: "chat_reply",
                  message: typeof parsed.error === "string" ? parsed.error : "An error occurred.",
                  cards: [],
                });
              }
            }
          } catch {
            // Raw text fallback if JSON parsing fails
          }
        }
      }
    } catch (err) {
      if (onError) {
        onError(err);
      } else {
        throw err;
      }
    }
  },

  /**
   * Fetches active negotiations for a merchant.
   * @param {number} merchantId
   * @returns {Promise<Array>}
   */
  async getMerchantNegotiations(merchantId) {
    const res = await apiClient.get(`/negotiations/merchant/${merchantId}`);
    return res.data;
  },

  /**
   * Fetches all conversation transcripts for merchant oversight.
   * @returns {Promise<Array>}
   */
  async getMerchantTranscripts() {
    const res = await apiClient.get("/transcripts");
    return res.data;
  },

  /**
   * Updates merchant dynamic pricing bounds.
   * @param {Object} bounds
   * @returns {Promise<Object>}
   */
  async updatePricingBounds(bounds) {
    const res = await apiClient.put("/merchant/pricing-bounds", bounds);
    return res.data;
  },
};
