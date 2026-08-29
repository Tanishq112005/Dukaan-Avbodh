import { useState, useEffect, useCallback, useRef } from 'react';
import { useStore } from '../store/useStore';

export function useAgent() {
  const user = useStore(state => state.user);
  const cart = useStore(state => state.cart); // For context
  
  const [messages, setMessages] = useState([]);
  const [comboOffer, setComboOffer] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Sirf tabhi connect karo jab user logged in ho
    if (!user || !user.id) return;

    // Connect to FastAPI WebSocket
    const socketUrl = `ws://localhost:8000/ws/chat/${user.id}`;
    ws.current = new WebSocket(socketUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      console.log("Agent Connected to WebSocket");
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Agent ka reply aaya (Normal chat ya Proactive suggestion)
        if (data.type === 'chat_reply' || data.type === 'proactive_suggestion') {
          setMessages(prev => [...prev, { sender: 'ai', text: data.message }]);
          
          // Agar usne koi discount combo bheja hai, toh usko alag state mein save karo UI ke liye
          if (data.combo_offer) {
            setComboOffer(data.combo_offer);
          }
        }
      } catch (err) {
        console.error("Error parsing websocket message:", err);
      }
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      console.log("Agent Disconnected");
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [user]); // Re-run agar user change ho (login/logout)

  // Function to send a text message to the AI
  const sendMessage = useCallback((text) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(text);
      setMessages(prev => [...prev, { sender: 'user', text }]); // Add to local chat UI
    } else {
        console.warn("WebSocket is not open");
    }
  }, []);

  // Function to send background monitoring events (e.g. idle timeout, viewed product)
  const sendEvent = useCallback((eventName) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const payload = {
        type: 'monitoring_event',
        event: eventName,
        cart: cart // Agent ko current cart pass kar rahe hain
      };
      ws.current.send(JSON.stringify(payload));
    }
  }, [cart]);

  return {
    messages,
    sendMessage,
    sendEvent,
    isConnected,
    comboOffer,
    setComboOffer // So UI can clear it if dismissed
  };
}
