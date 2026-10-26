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
  const {
    aiMessages,
    isAiTyping,
    sendAiMessage,
    isAiConnected,
    comboOffer,
    connectAgent,
    disconnectAgent,
    isAgentOpen,
    setIsAgentOpen,
    openPaymentLink,
    pollPaymentStatus,
    startNewChat,
  } = useStore();

  useEffect(() => {
    connectAgent();

    // Clean up any stale or interrupted streaming placeholders restored from localStorage on initial mount
    const state = useStore.getState();
    const lastUpdated = state.aiMessagesLastUpdated;
    if (lastUpdated && (Date.now() - lastUpdated > 24 * 60 * 60 * 1000)) {
      useStore.setState({
        aiMessages: [],
        aiMessagesLastUpdated: Date.now(),
        comboOffer: null,
        isAiTyping: false,
      });
    } else {
      useStore.setState((s) => ({
        aiMessages: (s.aiMessages || [])
          .filter((m) => !(m.isStreaming && !m.text))
          .map((m) => (m.isStreaming ? { ...m, isStreaming: false, streamingStatus: null } : m)),
        isAiTyping: false,
        aiMessagesLastUpdated: lastUpdated || Date.now(),
      }));
    }

    return () => disconnectAgent();
  }, [connectAgent, disconnectAgent]);

  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      const isStreaming = aiMessages.some((m) => m.isStreaming);
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: isStreaming ? 'auto' : 'smooth',
      });
    }
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

  // Lock body scroll on mobile or in full screen when chat is open
  useEffect(() => {
    const isMobile = window.innerWidth < 640;
    if (isAgentOpen && (isFullScreen || isMobile)) {
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
    if (input.trim()) {
      sendAiMessage(input);
      setInput('');
    }
  };

  const handleProductClick = () => {
    if (isFullScreen) {
      setIsFullScreen(false);
    }
  };

  return (
    <>
      {isAgentOpen && (
        <div
          className={cn(
            "fixed z-50 flex flex-col transition-all duration-300",
            // On mobile: occupy full screen smoothly like a native app
            // On desktop: float cleanly at bottom-right or full screen if toggled
            isFullScreen
              ? "inset-0 items-stretch bg-[#FBF8F3]"
              : "inset-0 sm:inset-auto sm:bottom-6 sm:right-6 sm:items-end"
          )}
        >
          <div
            className={cn(
              "flex flex-col overflow-hidden bg-white",
              isFullScreen
                ? "flex-1 w-full h-full bg-[#FBF8F3]"
                : "w-full h-full sm:w-[420px] sm:h-[72vh] sm:rounded-[28px] sm:border sm:border-stone-200/80 sm:shadow-[0_24px_80px_-24px_rgba(20,16,12,0.45)] sm:mb-2"
            )}
          >
            <ChatHeader
              isAiConnected={isAiConnected}
              setIsAgentOpen={(v) => { setIsAgentOpen(v); setIsFullScreen(false); }}
              isFullScreen={isFullScreen}
              setIsFullScreen={setIsFullScreen}
              startNewChat={startNewChat}
            />
            <div className={cn("flex-1 overflow-hidden flex flex-col", isFullScreen ? "max-w-4xl mx-auto w-full" : "")}>
              <ChatMessages
                aiMessages={aiMessages}
                isAiTyping={isAiTyping}
                comboOffer={comboOffer}
                chatContainerRef={chatContainerRef}
                renderMessage={renderMessage}
                onPayClick={openPaymentLink}
                onProductClick={handleProductClick}
                isFullScreen={isFullScreen}
              />
            </div>
            <div className={cn(isFullScreen ? "bg-[#FBF8F3]" : "")}>
              <ChatInput
                input={input}
                setInput={setInput}
                handleSend={handleSend}
                isAiConnected={isAiConnected}
                isFullScreen={isFullScreen}
              />
            </div>
          </div>
        </div>
      )}

      {/* Floating launcher button when chat is minimized/closed */}
      {!isAgentOpen && (
        <div className="fixed bottom-5 right-5 sm:bottom-6 sm:right-6 z-40 flex items-center gap-3">
          <button
            onClick={() => setIsAgentOpen(true)}
            className="hidden sm:flex items-center gap-2 bg-white/95 backdrop-blur border border-stone-200/90 shadow-[0_8px_30px_rgb(0,0,0,0.12)] px-4 py-2.5 rounded-full text-xs font-semibold text-stone-800 hover:bg-stone-50 transition-all hover:scale-105 cursor-pointer"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Chat with Atelier Stylist</span>
          </button>
          <button
            onClick={() => setIsAgentOpen(true)}
            aria-label="Open AI Stylist Chat"
            title="Chat with AI Stylist"
            className="bg-stone-900 hover:bg-[#6e1423] text-white p-3.5 sm:p-4 rounded-full shadow-[0_12px_40px_-8px_rgba(20,16,12,0.6)] transition-all hover:scale-110 flex items-center justify-center relative cursor-pointer"
          >
            <MessageCircle size={22} />
            <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C45C26] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-[#C45C26]"></span>
            </span>
          </button>
        </div>
      )}
    </>
  );
}
