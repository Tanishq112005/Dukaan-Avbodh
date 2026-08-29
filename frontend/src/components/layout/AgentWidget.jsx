import React, { useState, useRef, useEffect } from 'react';
import { useAgent } from '../../hooks/useAgent';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Shadcn-style utility for class merging
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function AgentWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const { messages, sendMessage, isConnected, comboOffer } = useAgent();
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div className="mb-4 w-80 sm:w-96 bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 transform origin-bottom-right">
          
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-100 p-1.5 rounded-full">
                <Bot size={18} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 text-sm">Dukaan AI Agent</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-green-500" : "bg-red-500")} />
                  <p className="text-[10px] uppercase font-medium tracking-wide text-slate-500">
                    {isConnected ? 'Online (Proactive)' : 'Offline'}
                  </p>
                </div>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-md transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 h-[350px] overflow-y-auto p-4 space-y-4 bg-white/50">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3">
                <div className="bg-slate-50 p-4 rounded-full">
                  <MessageCircle size={32} className="text-slate-300" />
                </div>
                <p className="text-sm text-center px-4">
                  Hi! I'm your AI shopping assistant.<br/>Ask me for a discount, outfit suggestions, or styling help!
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={cn("flex gap-2", msg.sender === 'user' ? "flex-row-reverse" : "")}>
                  <div className={cn(
                    "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1",
                    msg.sender === 'user' ? "bg-slate-100" : "bg-indigo-50"
                  )}>
                    {msg.sender === 'user' ? <User size={13} className="text-slate-600"/> : <Bot size={13} className="text-indigo-600"/>}
                  </div>
                  <div className={cn(
                    "px-3.5 py-2 rounded-2xl max-w-[80%] text-sm shadow-sm",
                    msg.sender === 'user' 
                      ? "bg-slate-900 text-white rounded-tr-sm" 
                      : "bg-white border border-slate-100 text-slate-800 rounded-tl-sm"
                  )}>
                    {msg.text}
                  </div>
                </div>
              ))
            )}
            
            {/* Combo Offer Banner */}
            {comboOffer && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-sm text-emerald-800 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-lg">🎉</span>
                  <strong className="font-semibold tracking-tight">Limited Combo Offer!</strong>
                </div>
                <p className="opacity-90">
                  Buy {comboOffer.products.join(" + ")} together for a <span className="font-bold">{comboOffer.effective_discount_percent}%</span> discount!
                </p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!isConnected}
              placeholder="Ask for a discount..."
              className="flex-1 bg-slate-50 border border-slate-200 rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
            />
            <button 
              type="submit" 
              disabled={!isConnected || !input.trim()}
              className="bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white p-2.5 rounded-full shadow-sm transition-all flex-shrink-0"
            >
              <Send size={16} className="ml-0.5" />
            </button>
          </form>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-slate-900 hover:bg-slate-800 text-white p-4 rounded-full shadow-lg shadow-slate-900/20 transition-all hover:scale-105 active:scale-95 flex items-center justify-center"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>
    </div>
  );
}
