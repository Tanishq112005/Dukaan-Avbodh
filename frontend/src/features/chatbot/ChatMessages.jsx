import React from 'react';
import { MessageCircle, Bot, User, Loader2 } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ProductCard } from "../../components/ui/ProductCard";
import { ComboBanner } from "./ComboBanner";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatMessages({ aiMessages, isAiTyping, comboOffer, messagesEndRef, renderMessage }) {
  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4 bg-white/50">
      {aiMessages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-3">
          <div className="bg-slate-50 p-4 rounded-full"><MessageCircle size={32} className="text-slate-300" /></div>
          <p className="text-sm text-center px-4">Hi! I'm your AI shopping assistant.<br/>Ask me for a discount!</p>
        </div>
      ) : (
        aiMessages.map((msg, idx) => (
          <div key={idx} className={cn("flex gap-2", msg.sender === 'user' ? "flex-row-reverse" : "")}>
            <div className={cn("flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1", msg.sender === 'user' ? "bg-slate-100" : "bg-indigo-50")}>
              {msg.sender === 'user' ? <User size={13} className="text-slate-600"/> : <Bot size={13} className="text-indigo-600"/>}
            </div>
            <div className={cn("px-3.5 py-2 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed", msg.sender === 'user' ? "bg-slate-900 text-white rounded-tr-sm" : "bg-white border border-slate-100 text-slate-800 rounded-tl-sm")}>
              <div className="whitespace-pre-wrap">{renderMessage(msg.text)}</div>
              {msg.suggested_products && msg.suggested_products.length > 0 && (
                <div className="mt-3 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                  {msg.suggested_products.map(p => (
                    <ProductCard key={p.id} size="small" {...p} image_url={p.image_url || p.image} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))
      )}
      {isAiTyping && (
        <div className="flex gap-2">
          <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1 bg-indigo-50"><Bot size={13} className="text-indigo-600"/></div>
          <div className="px-3.5 py-3 rounded-2xl max-w-[80%] text-sm shadow-sm bg-white border border-slate-100 text-slate-800 rounded-tl-sm flex items-center gap-2">
            <Loader2 size={14} className="animate-spin text-slate-400" /><span className="text-slate-400">Agent is typing...</span>
          </div>
        </div>
      )}
      <ComboBanner comboOffer={comboOffer} />
      <div ref={messagesEndRef} />
    </div>
  );
}
