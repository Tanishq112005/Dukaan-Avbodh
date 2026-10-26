import React, { useMemo } from 'react';
import { MessageCircle, Bot, User, Loader2, Sparkles, Tag, Package, Compass } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ComboBanner } from "./ComboBanner";
import { AiCard } from "./cards/CardRegistry";

function cn(...inputs) { return twMerge(clsx(inputs)); }

// Extracted + memoized: only re-renders if ITS OWN props change
const ChatMessageItem = React.memo(function ChatMessageItem({ msg, renderMessage, onPayClick, onProductClick, onAction }) {
  // Normalize and synthesize purpose-built cards for any data in the message
  const cards = useMemo(() => {
    const list = Array.isArray(msg.cards) ? [...msg.cards] : [];

    // 1. Synthesize Recommendation Card from suggested_products if not already present
    if (
      !list.some((c) => c.type === "recommendation") &&
      Array.isArray(msg.suggested_products) &&
      msg.suggested_products.length > 0
    ) {
      const products = msg.suggested_products.map((raw) =>
        raw?.product ? { ...raw.product, id: raw.product.id || raw.product_id } : raw
      );
      list.push({
        type: "recommendation",
        data: {
          title: "Stylist Recommendations",
          products,
        },
      });
    }

    // 2. Synthesize Payment Card from payment_link if not already present
    if (!list.some((c) => c.type === "payment") && msg.payment_link && !msg.payment_confirmed) {
      list.push({
        type: "payment",
        data: {
          title: "Secure Order Checkout",
          payment_link: msg.payment_link,
          amount: msg.total_amount || msg.amount,
          cart: msg.cart_items || msg.cart,
        },
      });
    }

    // 3. Synthesize Order Confirmation Card from payment_confirmed
    if (!list.some((c) => c.type === "order_confirmed") && msg.payment_confirmed) {
      list.push({
        type: "order_confirmed",
        data: {
          title: "Payment Confirmed · Order Placed",
          order_id: msg.order_id || "CONFIRMED",
          amount: msg.total_amount || msg.amount,
        },
      });
    }

    // 4. Synthesize Negotiation Card if discount or combo offer is present
    if (
      !list.some((c) => c.type === "negotiation") &&
      (msg.combo_offer || (msg.current_discount_percent && msg.current_discount_percent > 0))
    ) {
      list.push({
        type: "negotiation",
        data: {
          title: "VIP Price Offer",
          discount_percent: msg.current_discount_percent || 10,
          combo_offer: msg.combo_offer,
          offer_price: msg.offer_price || msg.discounted_price,
          original_price: msg.original_price,
          savings: msg.savings,
          status: "active",
        },
      });
    }

    // 5. Synthesize Order Tracking Card if order tracking info is present
    if (!list.some((c) => c.type === "order_tracking") && (msg.order_status || msg.orders)) {
      const activeOrder = Array.isArray(msg.orders) ? msg.orders[0] : null;
      list.push({
        type: "order_tracking",
        data: {
          title: "Live Order Tracking",
          order_id: msg.order_id || activeOrder?.id || "ORD-RECENT",
          status: msg.order_status || activeOrder?.status || "Dispatched",
          delivery_estimate: msg.delivery_estimate || "Expected in 2-3 Days",
          items: msg.order_items || activeOrder?.items || [],
        },
      });
    }

    // 6. Synthesize Size Advisor Card if sizing info is present
    if (!list.some((c) => c.type === "size_advisor") && msg.size_recommendation) {
      list.push({
        type: "size_advisor",
        data: {
          recommended_size: msg.size_recommendation.size || msg.size_recommendation,
          product: msg.size_recommendation.product || msg.product,
          fit_type: msg.size_recommendation.fit_type || "True to Size · Regular Fit",
          rationale: msg.size_recommendation.rationale,
        },
      });
    }

    // 7. Synthesize Combo Lookbook Card if lookbook items are present
    if (!list.some((c) => c.type === "combo_lookbook") && msg.combo_lookbook) {
      list.push({
        type: "combo_lookbook",
        data: {
          title: msg.combo_lookbook.title || "Curated Outfit Ensemble",
          items: msg.combo_lookbook.items || [],
          discount_percent: msg.combo_lookbook.discount_percent || 15,
          combo_price: msg.combo_lookbook.combo_price,
        },
      });
    }

    return list;
  }, [msg]);

  const hasCards = cards.length > 0;

  return (
    <div className={cn("flex gap-2.5", msg.sender === 'user' ? "flex-row-reverse" : "")}>
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center mt-1 shadow-xs",
        msg.sender === 'user'
          ? "bg-stone-900 text-white"
          : "bg-gradient-to-tr from-[#6e1423] to-[#C45C26] text-white"
      )}>
        {msg.sender === 'user' ? <User size={13} /> : <Bot size={14} className="text-white"/>}
      </div>

      {/* Message Bubble Container */}
      <div className={cn(
        "rounded-2xl max-w-[90%] sm:max-w-[85%] text-xs sm:text-sm leading-relaxed transition-all shadow-xs",
        msg.sender === 'user'
          ? "bg-stone-900 text-white rounded-tr-xs px-4 py-2.5"
          : "bg-white border border-stone-200/90 text-stone-800 rounded-tl-xs p-3.5 sm:p-4"
      )}>
        {/* Streaming Thinking State */}
        {msg.streamingStatus && !msg.text ? (
          <div className="flex items-center gap-2.5 text-xs text-stone-600 py-1 transition-all duration-300">
            <div className="relative flex items-center justify-center w-4 h-4 flex-shrink-0">
              <span className="absolute inline-flex h-full w-full rounded-full bg-[#C45C26]/25 animate-ping" />
              <Loader2 size={13} className="animate-spin text-[#C45C26] relative z-10" />
            </div>
            <span className="font-medium tracking-wide text-stone-700 animate-pulse">
              {msg.streamingStatus}
            </span>
          </div>
        ) : (
          <div className="whitespace-pre-wrap font-normal">
            {renderMessage(msg.text, msg.payment_link)}
            {msg.isStreaming && (
              <span className="inline-block w-1.5 h-3.5 ml-1 bg-[#C45C26] animate-pulse align-middle rounded-sm" />
            )}
          </div>
        )}

        {/* Generative UI Purpose-Built Cards */}
        {hasCards && (
          <div className="space-y-3 mt-3">
            {cards.map((card, idx) => (
              <AiCard
                key={card.id || `card-${card.type}-${idx}`}
                card={card}
                onProductClick={onProductClick}
                onPayClick={onPayClick}
                onAction={onAction}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

export function ChatMessages({
  aiMessages,
  isAiTyping,
  comboOffer,
  chatContainerRef,
  renderMessage,
  onPayClick,
  onProductClick,
  onAction,
  onQuickPrompt,
  isFullScreen,
}) {
  const renderedMessages = useMemo(() => (
    aiMessages.map((msg, idx) => (
      <ChatMessageItem
        key={msg.id ?? `msg-${idx}`}
        msg={msg}
        renderMessage={renderMessage}
        onPayClick={onPayClick}
        onProductClick={onProductClick}
        onAction={onAction}
      />
    ))
  ), [aiMessages, renderMessage, onPayClick, onProductClick, onAction]);

  const hasStreamingMessage = useMemo(
    () => aiMessages.some((m) => m.isStreaming),
    [aiMessages]
  );

  const starterPrompts = [
    { icon: Sparkles, title: "Style an Outfit", prompt: "Recommend a luxury curated outfit pairing for this weekend." },
    { icon: Tag, title: "VIP Bargain", prompt: "Can you offer me an exclusive VIP bundle discount on my cart?" },
    { icon: Compass, title: "Top Collections", prompt: "Show me the top-rated new apparel drops in the catalog." },
    { icon: Package, title: "Track Orders", prompt: "Check the delivery and tracking status of my recent orders." },
  ];

  return (
    <div
      ref={chatContainerRef}
      className={cn(
        "flex-1 overflow-y-auto custom-scrollbar space-y-5 bg-[#FBF8F3]",
        isFullScreen ? "px-6 sm:px-12 md:px-16 py-8" : "p-4"
      )}
    >
      {aiMessages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-stone-500 py-6 px-3">
          <div className="relative mb-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#6e1423] to-[#C45C26] text-white flex items-center justify-center shadow-lg">
              <Bot size={28} />
            </div>
            <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full flex items-center justify-center">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
            </span>
          </div>

          <h3 className="font-display text-base sm:text-lg font-bold uppercase tracking-tight text-stone-900 text-center">
            Dukaan Atelier AI Stylist
          </h3>
          <p className="text-xs text-center text-stone-500 max-w-xs mt-1 mb-6 leading-relaxed">
            Your autonomous agent for runway curation, sizing guidance, and live merchant price negotiation.
          </p>

          {/* Quick Starter Cards */}
          <div className="grid grid-cols-2 gap-2.5 w-full max-w-sm">
            {starterPrompts.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onQuickPrompt?.(item.prompt)}
                  className="bg-white border border-stone-200/90 hover:border-stone-400 p-3 rounded-xl text-left hover:shadow-xs transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <Icon size={14} className="text-[#C45C26] mb-1.5 group-hover:scale-110 transition-transform" />
                  <p className="font-semibold text-xs text-stone-900 group-hover:text-[#6e1423] transition-colors leading-tight">
                    {item.title}
                  </p>
                  <p className="text-[10px] text-stone-400 mt-0.5 truncate">
                    {item.prompt}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        renderedMessages
      )}

      {isAiTyping && !hasStreamingMessage && (
        <div className="flex gap-2.5">
          <div className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center mt-1 bg-gradient-to-tr from-[#6e1423] to-[#C45C26] text-white shadow-xs">
            <Bot size={14} className="text-white"/>
          </div>
          <div className="px-4 py-3 rounded-2xl max-w-[80%] text-xs sm:text-sm shadow-xs bg-white border border-stone-200/90 text-stone-800 rounded-tl-xs flex items-center gap-2.5">
            <div className="relative flex items-center justify-center w-4 h-4 flex-shrink-0">
              <span className="absolute inline-flex h-full w-full rounded-full bg-[#C45C26]/25 animate-ping" />
              <Loader2 size={13} className="animate-spin text-[#C45C26] relative z-10" />
            </div>
            <span className="text-stone-600 font-medium text-xs animate-pulse">Stylist is thinking...</span>
          </div>
        </div>
      )}

      <ComboBanner comboOffer={comboOffer} />
    </div>
  );
}
