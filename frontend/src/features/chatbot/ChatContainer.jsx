import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, ArrowDown } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { useStore } from '../../store/useStore';
import { renderMessage } from './renderMessage';
import { ChatHeader } from './ChatHeader';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function AgentWidget() {
  const {
    isAgentOpen,
    setIsAgentOpen,
    isAiConnected,
    connectAgent,
    disconnectAgent,
    aiMessages,
    isAiTyping,
    sendAiMessage,
    startNewChat,
    comboOffer,
    openPaymentLink,
    pollPaymentStatus,
  } = useStore();

  const [input, setInput] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false);

  useEffect(() => {
    connectAgent();

    // Hydrate state from localStorage if available
    const stored = localStorage.getItem('dukaan-store');
    if (stored) {
      const parsed = JSON.parse(stored);
      const cachedMessages = parsed.state?.aiMessages || [];
      const lastUpdated = parsed.state?.aiMessagesLastUpdated;
      useStore.setState((state) => ({
        ...state,
        aiMessages: cachedMessages.length > 0 ? cachedMessages : state.aiMessages,
        aiMessagesLastUpdated: lastUpdated || Date.now(),
      }));
    }

    return () => disconnectAgent();
  }, [connectAgent, disconnectAgent]);

  const chatContainerRef = useRef(null);
  const userScrolledUpRef = useRef(false);
  const rafIdRef = useRef(null);
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);

  // Monitor user manual scrolling on the chat container
  useEffect(() => {
    const el = chatContainerRef.current;
    if (!el) return;

    const handleScroll = () => {
      // Calculate distance from bottom
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      // If user scrolls up by more than 70px, pause auto-scroll so they can read freely
      const scrolledUp = distanceFromBottom > 70;
      userScrolledUpRef.current = scrolledUp;
      setIsUserScrolledUp(scrolledUp);
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      el.removeEventListener('scroll', handleScroll);
    };
  }, [isAgentOpen]);

  // Handle smooth stream-following without jerky snapping or fighting user scrolling
  useEffect(() => {
    const el = chatContainerRef.current;
    if (!el || userScrolledUpRef.current) return;

    const isStreaming = aiMessages.some((m) => m.isStreaming);

    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
    }

    rafIdRef.current = requestAnimationFrame(() => {
      if (!el || userScrolledUpRef.current) return;
      if (isStreaming) {
        // Direct scrollTop in rAF follows the stream smoothly without fighting smooth-scroll queues
        el.scrollTop = el.scrollHeight;
      } else {
        el.scrollTo({
          top: el.scrollHeight,
          behavior: 'smooth',
        });
      }
    });

    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [aiMessages, isAgentOpen]);

  const scrollToBottom = () => {
    userScrolledUpRef.current = false;
    setIsUserScrolledUp(false);
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  };

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
      userScrolledUpRef.current = false;
      setIsUserScrolledUp(false);
      sendAiMessage(input);
      setInput('');
    }
  };

  const handleQuickPrompt = (prompt) => {
    if (prompt) {
      userScrolledUpRef.current = false;
      setIsUserScrolledUp(false);
      sendAiMessage(prompt);
    }
  };

  const handleAction = (actionType, payload) => {
    if (actionType === "accept_offer") {
      const discount = payload?.discountPercent || 10;
      sendAiMessage(`Deal accepted! Applying the ${discount}% VIP discount.`);
    }
  };

  const handleProductClick = () => {
    if (isFullScreen) {
      setIsFullScreen(false);
    }
    if (window.innerWidth < 640) {
      setIsAgentOpen(false);
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
                ? "flex-1 w-full h-[100dvh] sm:h-full bg-[#FBF8F3]"
                : "w-full h-[100dvh] sm:w-[440px] sm:h-[75vh] sm:rounded-[28px] sm:border sm:border-stone-200/80 sm:shadow-[0_24px_80px_-24px_rgba(20,16,12,0.45)] sm:mb-2"
            )}
          >
            <ChatHeader
              isAiConnected={isAiConnected}
              setIsAgentOpen={(v) => { setIsAgentOpen(v); setIsFullScreen(false); }}
              isFullScreen={isFullScreen}
              setIsFullScreen={setIsFullScreen}
              startNewChat={startNewChat}
            />
            <div className={cn("flex-1 overflow-hidden flex flex-col relative", isFullScreen ? "max-w-4xl mx-auto w-full" : "")}>
              <ChatMessages
                aiMessages={aiMessages}
                isAiTyping={isAiTyping}
                comboOffer={comboOffer}
                chatContainerRef={chatContainerRef}
                renderMessage={renderMessage}
                onPayClick={openPaymentLink}
                onProductClick={handleProductClick}
                onQuickPrompt={handleQuickPrompt}
                onAction={handleAction}
                isFullScreen={isFullScreen}
              />

              {/* Floating Jump to Bottom Button when user is scrolled up */}
              {isUserScrolledUp && (
                <button
                  type="button"
                  onClick={scrollToBottom}
                  className="absolute bottom-3 right-1/2 translate-x-1/2 z-20 px-3.5 py-1.5 rounded-full bg-white/95 hover:bg-stone-50 border border-stone-200/90 text-stone-700 text-xs font-semibold shadow-md flex items-center gap-1.5 transition-all duration-200 cursor-pointer animate-in fade-in"
                >
                  <ArrowDown size={13} className="text-[#C45C26]" />
                  <span>Resume chat</span>
                  {aiMessages.some((m) => m.isStreaming) && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[#C45C26] animate-pulse" />
                  )}
                </button>
              )}
            </div>
            <div className={cn(isFullScreen ? "bg-[#FBF8F3]" : "")}>
              <ChatInput
                input={input}
                setInput={setInput}
                handleSend={handleSend}
                isAiConnected={isAiConnected}
                isFullScreen={isFullScreen}
                onQuickPrompt={handleQuickPrompt}
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
