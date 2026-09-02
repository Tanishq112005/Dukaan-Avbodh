import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { ChatHeader } from "./ChatHeader";
import { renderMessage } from "./renderMessage";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function AgentWidget() {
  const [input, setInput] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false);
  const { aiMessages, aiMessagesLastUpdated, isAiTyping, sendAiMessage, isAiConnected, comboOffer, connectAgent, disconnectAgent, isAgentOpen, setIsAgentOpen, openPaymentLink, pollPaymentStatus, startNewChat } = useStore();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    connectAgent();
    if (aiMessagesLastUpdated && (Date.now() - aiMessagesLastUpdated > 24 * 60 * 60 * 1000)) {
      useStore.setState({ aiMessages: [], aiMessagesLastUpdated: Date.now(), comboOffer: null });
    } else if (!aiMessagesLastUpdated) {
      useStore.setState({ aiMessagesLastUpdated: Date.now() });
    }
    return () => disconnectAgent();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [aiMessages, isAgentOpen, isAiTyping]);

  useEffect(() => {
    const onFocus = () => pollPaymentStatus();
    const onVisibility = () => {
      if (document.visibilityState === 'visible') pollPaymentStatus();
    };
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [pollPaymentStatus]);

  useEffect(() => {
    if (isAgentOpen && isFullScreen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isFullScreen, isAgentOpen]);

  const handleSend = (e) => {
    e.preventDefault();
    if (input.trim()) { sendAiMessage(input); setInput(''); }
  };

  return (
    <div className={cn("fixed z-50 flex flex-col", isFullScreen ? "inset-0 items-stretch bg-[#FBF8F3]" : "bottom-6 right-6 items-end")}>
      {isAgentOpen && (
        <div className={cn(
          "flex flex-col transition-all duration-300 overflow-hidden",
          isFullScreen
            ? "flex-1 w-full h-full bg-[#FBF8F3]"
            : "bg-white mb-4 w-[92vw] sm:w-[420px] border border-stone-200/80 rounded-[28px] shadow-[0_24px_80px_-24px_rgba(20,16,12,0.45)] h-[72vh]"
        )}>
          <ChatHeader isAiConnected={isAiConnected} setIsAgentOpen={(v) => { setIsAgentOpen(v); setIsFullScreen(false); }} isFullScreen={isFullScreen} setIsFullScreen={setIsFullScreen} startNewChat={startNewChat} />
          <div className={cn("flex-1 overflow-hidden flex flex-col", isFullScreen ? "max-w-4xl mx-auto w-full" : "")}>
            <ChatMessages aiMessages={aiMessages} isAiTyping={isAiTyping} comboOffer={comboOffer} messagesEndRef={messagesEndRef} renderMessage={renderMessage} onPayClick={openPaymentLink} isFullScreen={isFullScreen} />
          </div>
          <div className={cn(isFullScreen ? "bg-[#FBF8F3]" : "")}>
            <ChatInput input={input} setInput={setInput} handleSend={handleSend} isAiConnected={isAiConnected} isFullScreen={isFullScreen} />
          </div>
        </div>
      )}
      {!isFullScreen && (
        <button
          onClick={() => setIsAgentOpen(!isAgentOpen)}
          className="bg-stone-900 hover:bg-stone-800 text-white p-4 rounded-full shadow-[0_12px_40px_-8px_rgba(20,16,12,0.6)] transition-transform hover:scale-105 flex items-center justify-center"
        >
          {isAgentOpen ? <X size={24} /> : <MessageCircle size={24} />}
        </button>
      )}
    </div>
  );
}
