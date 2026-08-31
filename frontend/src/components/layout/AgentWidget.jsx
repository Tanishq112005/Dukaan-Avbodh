import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { MessageCircle, X, Send, Bot, User, Loader2 } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Shadcn-style utility for class merging
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function AgentWidget() {
  const [input, setInput] = useState('');
  
  const { 
    user,
    aiMessages, 
    aiMessagesLastUpdated,
    isAiTyping,
    sendAiMessage, 
    isAiConnected, 
    comboOffer,
    connectAgent,
    disconnectAgent,
    isAgentOpen,
    setIsAgentOpen
  } = useStore();
  
  const messagesEndRef = useRef(null);

  // Connect once on mount, disconnect on unmount
  useEffect(() => {
    connectAgent();
    // Check if aiMessages are older than 1 day
    if (aiMessagesLastUpdated) {
      const now = Date.now();
      const diff = now - aiMessagesLastUpdated;
      if (diff > 24 * 60 * 60 * 1000) {
        useStore.setState({ aiMessages: [], aiMessagesLastUpdated: now, comboOffer: null });
      }
    } else {
      useStore.setState({ aiMessagesLastUpdated: Date.now() });
    }
    return () => disconnectAgent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [aiMessages, isAgentOpen, isAiTyping]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendAiMessage(input);
      setInput('');
    }
  };

  const renderMessage = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, i) => {
      const parts = line.split(/(\*\*.*?\*\*|\[.*?\]\(.*?\))/g);
      return (
        <React.Fragment key={i}>
          {parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="font-bold">{part.slice(2, -2)}</strong>;
            }
            const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
            if (linkMatch) {
              return (
                <a 
                  key={j} 
                  href={linkMatch[2]} 
                  className="text-indigo-600 hover:text-indigo-700 underline font-medium"
                >
                  {linkMatch[1]}
                </a>
              );
            }
            return <span key={j}>{part}</span>;
          })}
          {i < text.split('\n').length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isAgentOpen && (
        <div className="mb-4 w-[90vw] sm:w-[450px] bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 transform origin-bottom-right h-[70vh]">
          
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-100 p-1.5 rounded-full">
                <Bot size={18} className="text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800 text-sm">Dukkan AI Agent</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className={cn("w-2 h-2 rounded-full", isAiConnected ? "bg-green-500" : "bg-red-500")} />
                  <p className="text-[10px] uppercase font-medium tracking-wide text-slate-500">
                    {isAiConnected ? 'Online (Proactive)' : 'Offline'}
                  </p>
                </div>
              </div>
            </div>
            <button 
              onClick={() => setIsAgentOpen(false)}
              className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-md transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4 bg-white/50">
            {aiMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3">
                <div className="bg-slate-50 p-4 rounded-full">
                  <MessageCircle size={32} className="text-slate-300" />
                </div>
                <p className="text-sm text-center px-4">
                  Hi! I'm your AI shopping assistant.<br/>Ask me for a discount, outfit suggestions, or styling help!
                </p>
              </div>
            ) : (
              aiMessages.map((msg, idx) => (
                <div key={idx} className={cn("flex gap-2", msg.sender === 'user' ? "flex-row-reverse" : "")}>
                  <div className={cn(
                    "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1",
                    msg.sender === 'user' ? "bg-slate-100" : "bg-indigo-50"
                  )}>
                    {msg.sender === 'user' ? <User size={13} className="text-slate-600"/> : <Bot size={13} className="text-indigo-600"/>}
                  </div>
                  <div className={cn(
                    "px-3.5 py-2 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed",
                    msg.sender === 'user' 
                      ? "bg-slate-900 text-white rounded-tr-sm" 
                      : "bg-white border border-slate-100 text-slate-800 rounded-tl-sm"
                  )}>
                    <div className="whitespace-pre-wrap">
                      {renderMessage(msg.text)}
                    </div>
                    
                    {/* Render Rich Product Cards if they exist */}
                    {msg.suggested_products && msg.suggested_products.length > 0 && (
                      <div className="mt-3 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                        {msg.suggested_products.map(p => (
                          <a 
                            key={p.id} 
                            href={`/product/${p.id}`} 
                            className="flex-shrink-0 w-32 border border-slate-100 rounded-lg overflow-hidden block hover:border-indigo-200 transition-colors bg-slate-50 group"
                          >
                            <div className="relative h-28 bg-white">
                              <img 
                                src={p.image_url || p.image || `https://via.placeholder.com/150?text=${p.name.charAt(0)}`} 
                                alt={p.name} 
                                className="w-full h-full object-cover" 
                              />
                              <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <div className="p-2">
                              <p className="text-xs font-medium text-slate-800 truncate" title={p.name}>{p.name}</p>
                              <p className="text-[11px] font-bold text-slate-900 mt-0.5">₹{p.price}</p>
                            </div>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            
            {isAiTyping && (
              <div className="flex gap-2">
                <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1 bg-indigo-50">
                  <Bot size={13} className="text-indigo-600"/>
                </div>
                <div className="px-3.5 py-3 rounded-2xl max-w-[80%] text-sm shadow-sm bg-white border border-slate-100 text-slate-800 rounded-tl-sm flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-slate-400" />
                  <span className="text-slate-400">Agent is typing...</span>
                </div>
              </div>
            )}
            
            {/* Combo Offer Banner */}
            {comboOffer && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-sm text-emerald-800 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-lg">dYZ%</span>
                  <strong className="font-semibold tracking-tight">Limited Combo Offer!</strong>
                </div>
                <p className="opacity-90 mb-2">
                  Buy {comboOffer.products.map(p => p.name).join(" + ")} together for a <span className="font-bold">{Math.abs(comboOffer.effective_discount_percent).toFixed(2)}%</span> discount!
                </p>
                
                {/* Product Images Row */}
                <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                  {comboOffer.products.map(p => (
                    <a 
                      key={p.id} 
                      href={`/product/${p.id}`} 
                      title={p.name}
                      className="flex-shrink-0 relative group block"
                    >
                      <img 
                        src={p.image || `https://via.placeholder.com/60?text=${p.name.charAt(0)}`} 
                        alt={p.name} 
                        className="w-12 h-12 rounded-md object-cover border border-emerald-200 bg-white" 
                      />
                      <div className="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md" />
                    </a>
                  ))}
                </div>
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
              disabled={!isAiConnected}
              placeholder="Ask for a discount..."
              className="flex-1 bg-slate-50 border border-slate-200 rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
            />
            <button 
              type="submit" 
              disabled={!isAiConnected || !input.trim()}
              className="bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white p-2.5 rounded-full shadow-sm transition-all flex-shrink-0"
            >
              <Send size={16} className="ml-0.5" />
            </button>
          </form>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsAgentOpen(!isAgentOpen)}
        className="bg-slate-900 hover:bg-slate-800 text-white p-4 rounded-full shadow-lg shadow-slate-900/20 transition-all hover:scale-105 active:scale-95 flex items-center justify-center"
      >
        {isAgentOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>
    </div>
  );
}
