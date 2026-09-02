import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useStore } from '../../store/useStore';
import { Bot, User, Loader2, Send } from 'lucide-react';
import { renderMessage } from '../chatbot/renderMessage';

export function MerchantAgentTab() {
  const { token } = useStore();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: userText }]);
    setIsTyping(true);

    try {
      const res = await axios.post(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/merchant/chat`,
        { text: userText },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages(prev => [...prev, { 
        id: Date.now(), 
        sender: 'ai', 
        text: res.data.message 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        sender: 'ai', 
        text: "Sorry, I couldn't process your request. Ensure the merchant MCP server is running." 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Chat Messages */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[#FBF8F3]">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-stone-400 space-y-3">
            <div className="bg-white p-4 rounded-full shadow-sm border border-stone-100">
              <Bot size={32} className="text-[#000000]" />
            </div>
            <p className="text-sm text-center px-4 font-medium text-stone-500">
              Your Merchant AI Co-Pilot is online.<br/>Ask for analytics, create campaigns, or manage products.
            </p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${
                msg.sender === 'user' ? 'bg-black text-white' : 'bg-gray-200 text-black'
              }`}>
                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`px-4 py-3 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-black text-white rounded-tr-sm'
                  : 'bg-white border border-stone-100 text-stone-800 rounded-tl-sm'
              }`}>
                <div className="whitespace-pre-wrap">{renderMessage(msg.text)}</div>
              </div>
            </div>
          ))
        )}
        
        {isTyping && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 bg-gray-200 text-black">
              <Bot size={16} />
            </div>
            <div className="px-4 py-3 rounded-2xl max-w-[80%] text-sm shadow-sm bg-white border border-stone-100 text-stone-800 rounded-tl-sm flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-black" />
              <span className="text-stone-400">Co-Pilot is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSend} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a command (e.g. 'Show me total revenue', 'Create a 10% off campaign')"
            className="w-full pl-5 pr-14 py-3.5 bg-[#FBF8F3] border-none rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-black/5 placeholder:text-stone-400"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="absolute right-1.5 p-2 bg-black text-white rounded-full hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} className="ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
