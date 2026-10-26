import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { Bot, User, Loader2, Send, Sparkles } from 'lucide-react';
import { renderMessage } from '../chatbot/renderMessage';
import { agentService } from '../../services/agentService';

export function MerchantAgentTab() {
  const { token } = useStore();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const chatContainerRef = useRef(null);

  const quickPrompts = [
    "Which item is selling more this week?",
    "Show me total revenue and profit margin",
    "List products that are low in stock",
    "How much discount was given to customers?",
  ];

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

  const sendMessage = async (textToSend) => {
    if (!textToSend.trim() || isTyping) return;

    const userText = textToSend.trim();
    setInput('');
    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: userText }]);
    setIsTyping(true);

    try {
      const res = await agentService.sendMerchantMessage({ text: userText });

      setMessages(prev => [...prev, { 
        id: Date.now(), 
        sender: 'ai', 
        text: res.message || "Request completed." 
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

  const handleSend = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-[72vh] bg-white rounded-3xl shadow-sm border border-stone-200 overflow-hidden">
      {/* Chat Messages */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[#FBF8F3]">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-stone-400 space-y-4">
            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-sm border border-stone-200 text-stone-800">
              <Bot size={30} />
            </div>
            <div className="text-center px-4 max-w-md">
              <h4 className="font-bold text-stone-800 text-base mb-1">
                Merchant Intelligence Co-Pilot
              </h4>
              <p className="text-xs text-stone-500 leading-relaxed">
                Ask about real-time sales numbers, top sellers, automated discount limits, or inventory reorders.
              </p>
            </div>

            {/* Quick Prompts Chips */}
            <div className="flex flex-wrap gap-2 justify-center max-w-lg pt-2">
              {quickPrompts.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(qp)}
                  className="px-3.5 py-1.5 rounded-xl bg-white border border-stone-200 text-xs font-semibold text-stone-700 hover:border-black hover:text-black transition shadow-sm"
                >
                  ✨ {qp}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${
                msg.sender === 'user' ? 'bg-black text-white' : 'bg-stone-200 text-black'
              }`}>
                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`px-4 py-3 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-black text-white rounded-tr-sm'
                  : 'bg-white border border-stone-200 text-stone-800 rounded-tl-sm'
              }`}>
                <div className="leading-relaxed">{renderMessage(msg.text)}</div>
              </div>
            </div>
          ))
        )}
        
        {isTyping && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 bg-stone-200 text-black">
              <Bot size={16} />
            </div>
            <div className="px-4 py-3 rounded-2xl max-w-[80%] text-sm shadow-sm bg-white border border-stone-200 text-stone-800 rounded-tl-sm flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-black" />
              <span className="text-stone-400">Co-Pilot is calculating analytics...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-stone-100">
        <form onSubmit={handleSend} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your merchant assistant (e.g. 'Which item is selling more?', 'Show profit margin')..."
            className="w-full pl-5 pr-14 py-3.5 bg-[#FBF8F3] border border-stone-200 rounded-2xl text-sm focus:outline-none focus:ring-2 focus:ring-black placeholder:text-stone-400"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="absolute right-2 p-2.5 bg-black text-white rounded-xl hover:bg-stone-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
}
