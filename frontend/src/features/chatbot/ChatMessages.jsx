import React, { useMemo } from 'react';
import { MessageCircle, Bot, User, Loader2, ExternalLink } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ProductCard } from "../../components/ui/ProductCard";
import { ComboBanner } from "./ComboBanner";

function cn(...inputs) { return twMerge(clsx(inputs)); }

// Extracted + memoized: only re-renders if ITS OWN props change
const ChatMessageItem = React.memo(function ChatMessageItem({ msg, renderMessage, onPayClick }) {
  return (
    <div className={cn("flex gap-2", msg.sender === 'user' ? "flex-row-reverse" : "")}>
      <div className={cn(
        "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1",
        msg.sender === 'user' ? "bg-stone-900 text-white" : "bg-[#C45C26]/10"
      )}>
        {msg.sender === 'user' ? <User size={13} /> : <Bot size={13} className="text-[#C45C26]"/>}
      </div>
      <div className={cn(
        "px-3.5 py-2 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed",
        msg.sender === 'user'
          ? "bg-stone-900 text-white rounded-tr-sm"
          : "bg-white border border-stone-100 text-stone-800 rounded-tl-sm"
      )}>
        <div className="whitespace-pre-wrap">{renderMessage(msg.text, msg.payment_link)}</div>
        {msg.payment_link && (
          <button
            type="button"
            onClick={() => onPayClick?.(msg.payment_link)}
            className="mt-3 inline-flex items-center gap-2 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold tracking-wide uppercase px-3.5 py-2 rounded-full transition-colors"
          >
            Pay securely <ExternalLink size={12} />
          </button>
        )}
        {msg.suggested_products && msg.suggested_products.length > 0 && (
          <div className="mt-3 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {msg.suggested_products.map(p => (
              <ProductCard key={p.id} size="small" {...p} image_url={p.image_url || p.image} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

export function ChatMessages({ aiMessages, isAiTyping, comboOffer, chatContainerRef, renderMessage, onPayClick, isFullScreen }) {
  // Memoize the rendered list so it only recomputes when aiMessages actually changes
  const renderedMessages = useMemo(() => (
    aiMessages.map((msg, idx) => (
      <ChatMessageItem
        key={msg.id ?? idx}
        msg={msg}
        renderMessage={renderMessage}
        onPayClick={onPayClick}
      />
    ))
  ), [aiMessages, renderMessage, onPayClick]);

  return (
    <div ref={chatContainerRef} className={cn("flex-1 overflow-y-auto custom-scrollbar space-y-6 bg-[#FBF8F3]", isFullScreen ? "px-8 md:px-16 py-8" : "p-4")}>
      {aiMessages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-stone-400 space-y-3">
          <div className="bg-white p-4 rounded-full shadow-sm border border-stone-100">
            <MessageCircle size={32} className="text-[#C45C26]" />
          </div>
          <p className="text-sm text-center px-4 font-medium text-stone-500">
            Your personal stylist is here.<br/>Ask for looks, sizes, or a better price.
          </p>
        </div>
      ) : (
        renderedMessages
      )}
      {isAiTyping && (
        <div className="flex gap-2">
          <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1 bg-[#C45C26]/10">
            <Bot size={13} className="text-[#C45C26]"/>
          </div>
          <div className="px-3.5 py-3 rounded-2xl max-w-[80%] text-sm shadow-sm bg-white border border-stone-100 text-stone-800 rounded-tl-sm flex items-center gap-2">
            <Loader2 size={14} className="animate-spin text-[#C45C26]" />
            <span className="text-stone-400">Stylist is thinking...</span>
          </div>
        </div>
      )}
      <ComboBanner comboOffer={comboOffer} />
    </div>
  );
}