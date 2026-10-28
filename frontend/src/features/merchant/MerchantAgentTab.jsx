import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import {
  Bot,
  User,
  Loader2,
  Send,
  Sparkles,
  ShoppingBag,
  MessageSquare,
  TrendingUp,
  AlertTriangle,
  IndianRupee,
  Eye,
  CheckCircle2,
  Package,
} from 'lucide-react';
import { renderMessage } from '../chatbot/renderMessage';
import { agentService } from '../../services/agentService';

export function MerchantAgentTab() {
  const { token } = useStore();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [statusText, setStatusText] = useState('');
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const quickPrompts = [
    "Show me order history and total revenue received",
    "Inspect customer shopping chat sessions",
    "Which item is selling more this week?",
    "Show me total revenue and profit margin",
    "List products that are low in stock",
    "How much discount was given to customers?",
  ];

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, statusText]);

  const sendMessage = async (textToSend) => {
    if (!textToSend.trim() || isTyping) return;

    const userText = textToSend.trim();
    setInput('');
    const userMsgId = Date.now();
    const aiMsgId = userMsgId + 1;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: userText },
      { id: aiMsgId, sender: 'ai', text: '', cards: [], streaming: true },
    ]);
    setIsTyping(true);
    setStatusText('Co-Pilot is analyzing store operations...');

    let accumulatedText = '';
    let accumulatedCards = [];

    try {
      await agentService.streamMerchantMessage(
        { text: userText, accessToken: token },
        {
          onToken: (tok) => {
            accumulatedText += tok;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMsgId ? { ...m, text: accumulatedText } : m
              )
            );
          },
          onNodeUpdate: (node) => {
            if (node === 'tools') {
              setStatusText('Querying store databases and services...');
            } else if (node === 'agent') {
              setStatusText('Synthesizing executive store analysis...');
            } else if (node === 'post_process') {
              setStatusText('Finalizing executive report...');
            }
          },
          onToolCall: (toolName) => {
            const cleanTool = toolName.replace('merchant_', '').replace(/_/g, ' ');
            setStatusText(`Executing ${cleanTool}...`);
          },
          onCard: (cardOrCards) => {
            const cardsArray = Array.isArray(cardOrCards) ? cardOrCards : [cardOrCards];
            accumulatedCards = [...accumulatedCards, ...cardsArray];
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMsgId ? { ...m, cards: accumulatedCards } : m
              )
            );
          },
          onComplete: (payload) => {
            const finalText = payload.message || accumulatedText || "Request completed.";
            const finalCards = payload.cards || accumulatedCards || [];
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMsgId
                  ? { ...m, text: finalText, cards: finalCards, streaming: false }
                  : m
              )
            );
          },
          onError: (err) => {
            console.error("Merchant chat stream error:", err);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiMsgId
                  ? {
                      ...m,
                      text:
                        accumulatedText ||
                        "Sorry, I encountered an issue processing your request. Please ensure the backend is healthy.",
                      streaming: false,
                    }
                  : m
              )
            );
          },
        }
      );
    } catch (err) {
      console.error("Merchant chat invocation error:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId
            ? {
                ...m,
                text: "Sorry, I couldn't process your request. Ensure backend services are running.",
                streaming: false,
              }
            : m
        )
      );
    } finally {
      setIsTyping(false);
      setStatusText('');
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  // Helper renderer for Generative UI Cards
  const renderCard = (card, idx) => {
    if (!card || !card.type) return null;
    const { type, data } = card;

    // 1. Order History Card
    if (type === 'merchant_order_history') {
      return (
        <div key={idx} className="mt-3 p-4 bg-white rounded-2xl border border-stone-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2.5">
            <div className="flex items-center gap-2">
              <ShoppingBag size={18} className="text-[#C45C26]" />
              <h5 className="font-bold text-stone-800 text-sm">Order History & Total Received</h5>
            </div>
            <span className="text-[11px] font-mono font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded-lg border border-amber-200">
              {data.total_orders_received || 0} Orders
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            <div className="bg-stone-50 p-2.5 rounded-xl border border-stone-100">
              <span className="text-stone-400 block text-[10px] uppercase font-bold tracking-wider">Total Received</span>
              <span className="font-extrabold text-stone-900 text-sm">₹{(data.total_revenue_received_inr || 0).toLocaleString()}</span>
            </div>
            <div className="bg-stone-50 p-2.5 rounded-xl border border-stone-100">
              <span className="text-stone-400 block text-[10px] uppercase font-bold tracking-wider">Discounts Given</span>
              <span className="font-extrabold text-stone-900 text-sm">₹{(data.total_discounts_given_inr || 0).toLocaleString()}</span>
            </div>
            <div className="bg-stone-50 p-2.5 rounded-xl border border-stone-100 col-span-2 sm:col-span-1">
              <span className="text-stone-400 block text-[10px] uppercase font-bold tracking-wider">Status Breakdown</span>
              <div className="flex gap-1.5 flex-wrap mt-0.5">
                {Object.entries(data.status_breakdown || {}).map(([st, cnt]) => (
                  <span key={st} className="px-1.5 py-0.5 bg-white border border-stone-200 rounded text-[10px] font-bold text-stone-700">
                    {st}: {cnt}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {Array.isArray(data.orders) && data.orders.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-bold text-stone-500 block">Recent Received Orders:</span>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                {data.orders.slice(0, 5).map((ord, oIdx) => (
                  <div key={oIdx} className="flex items-center justify-between p-2 rounded-xl bg-stone-50 text-xs border border-stone-100">
                    <div>
                      <span className="font-bold text-stone-800">Order #{ord.order_id}</span>
                      <span className="text-stone-400 ml-2 text-[10px]">({ord.customer_name})</span>
                      <p className="text-[10px] text-stone-500 truncate max-w-[200px] sm:max-w-xs">{ord.products_summary}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <span className="font-bold text-stone-900 block">₹{ord.total_amount_inr}</span>
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                        ord.status === 'completed' || ord.status === 'paid'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {ord.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    // 2. Customer Chat Threads Card
    if (type === 'merchant_chat_threads') {
      return (
        <div key={idx} className="mt-3 p-4 bg-white rounded-2xl border border-stone-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2.5">
            <div className="flex items-center gap-2">
              <MessageSquare size={18} className="text-blue-600" />
              <h5 className="font-bold text-stone-800 text-sm">Customer Chat Sessions ({data.threads_count || 0})</h5>
            </div>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {(data.threads || []).slice(0, 5).map((th, tIdx) => (
              <div key={tIdx} className="p-2.5 rounded-xl bg-stone-50 border border-stone-100 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-stone-800">User #{th.user_id} &bull; <span className="font-mono text-[10px] text-stone-400">{th.thread_id}</span></span>
                  <button
                    onClick={() => sendMessage(`Show transcript for thread ${th.thread_id}`)}
                    className="text-[10px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <Eye size={12} /> View Dialog
                  </button>
                </div>
                {th.latest_user_message && (
                  <p className="text-[11px] text-stone-600 italic truncate">
                    &ldquo;{th.latest_user_message}&rdquo;
                  </p>
                )}
                <div className="flex items-center gap-2 text-[10px] text-stone-400">
                  <span>Messages: {th.messages_count}</span>
                  {th.negotiated_discount_percent > 0 && (
                    <span className="bg-amber-100 text-amber-800 px-1 rounded font-bold">
                      {th.negotiated_discount_percent}% Disc
                    </span>
                  )}
                  {th.order_placed && (
                    <span className="bg-emerald-100 text-emerald-800 px-1 rounded font-bold">
                      Order Placed
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // 3. Chat Transcript Card
    if (type === 'merchant_chat_transcript') {
      return (
        <div key={idx} className="mt-3 p-4 bg-white rounded-2xl border border-stone-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2.5">
            <div className="flex items-center gap-2">
              <MessageSquare size={18} className="text-purple-600" />
              <h5 className="font-bold text-stone-800 text-sm">Transcript: {data.thread_id}</h5>
            </div>
            <span className="text-[10px] font-mono text-stone-400">{data.message_count} messages</span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {(data.messages || []).map((m, mIdx) => (
              <div
                key={mIdx}
                className={`p-2 rounded-xl text-xs max-w-[90%] ${
                  m.sender === 'user' || m.sender === 'human'
                    ? 'bg-stone-900 text-white ml-auto rounded-tr-sm'
                    : 'bg-stone-100 text-stone-800 rounded-tl-sm'
                }`}
              >
                <span className="text-[9px] opacity-70 block font-bold uppercase">{m.sender}</span>
                <p className="leading-relaxed">{m.message}</p>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // 4. Analytics Snapshot Card
    if (type === 'merchant_analytics') {
      return (
        <div key={idx} className="mt-3 p-4 bg-white rounded-2xl border border-stone-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp size={18} className="text-emerald-600" />
              <h5 className="font-bold text-stone-800 text-sm">{data.title || "Store Analytics"}</h5>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider bg-stone-100 text-stone-600 px-2 py-0.5 rounded-lg">
              {data.time_range}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Gross Revenue</span>
              <span className="text-sm font-extrabold text-stone-900">₹{(data.gross_revenue_inr || 0).toLocaleString()}</span>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Net Profit</span>
              <span className="text-sm font-extrabold text-emerald-600">₹{(data.net_profit_inr || 0).toLocaleString()}</span>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Profit Margin</span>
              <span className="text-sm font-extrabold text-stone-900">{data.profit_margin_percent}%</span>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Total Orders</span>
              <span className="text-sm font-extrabold text-stone-900">{data.total_orders_count}</span>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Items Sold</span>
              <span className="text-sm font-extrabold text-stone-900">{data.total_items_sold}</span>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-xl">
              <span className="text-stone-400 text-[10px] uppercase font-bold block">Avg Order Value</span>
              <span className="text-sm font-extrabold text-stone-900">₹{Math.round(data.average_order_value_inr || 0)}</span>
            </div>
          </div>
        </div>
      );
    }

    // 5. Inventory Stock Alerts Card
    if (type === 'merchant_inventory_alerts') {
      return (
        <div key={idx} className="mt-3 p-4 bg-white rounded-2xl border border-stone-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-stone-100 pb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-500" />
              <h5 className="font-bold text-stone-800 text-sm">Inventory & Reorder Alerts</h5>
            </div>
            <div className="flex gap-1.5">
              <span className="text-[10px] font-bold bg-red-100 text-red-800 px-2 py-0.5 rounded">
                {data.out_of_stock_count || 0} Out of Stock
              </span>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                {data.low_stock_count || 0} Low Stock
              </span>
            </div>
          </div>
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {(data.critical_items || []).slice(0, 5).map((it, iIdx) => (
              <div key={iIdx} className="flex items-center justify-between p-2 rounded-xl bg-stone-50 text-xs">
                <span className="font-bold text-stone-800 truncate max-w-[200px]">{it.name}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  it.current_stock <= 0 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                }`}>
                  Stock: {it.current_stock}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Default fallback card
    return null;
  };

  return (
    <div className="flex flex-col h-[72vh] bg-white rounded-3xl shadow-sm border border-stone-200 overflow-hidden">
      {/* Chat Messages */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[#FBF8F3]"
      >
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
                Ask about real-time sales revenue, order history, customer bargaining sessions, or low inventory alerts.
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
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.sender === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${
                  msg.sender === 'user'
                    ? 'bg-black text-white'
                    : 'bg-stone-200 text-black'
                }`}
              >
                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div
                className={`px-4 py-3 rounded-2xl max-w-[85%] text-sm shadow-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-black text-white rounded-tr-sm'
                    : 'bg-white border border-stone-200 text-stone-800 rounded-tl-sm'
                }`}
              >
                {msg.text ? (
                  <div className="leading-relaxed">{renderMessage(msg.text)}</div>
                ) : (
                  msg.streaming && (
                    <div className="flex items-center gap-2 text-stone-400 py-1">
                      <Loader2 size={14} className="animate-spin text-stone-600" />
                      <span>{statusText || 'Co-Pilot is working on your request...'}</span>
                    </div>
                  )
                )}

                {/* Render Generative UI Cards */}
                {Array.isArray(msg.cards) &&
                  msg.cards.map((card, cIdx) => renderCard(card, cIdx))}
              </div>
            </div>
          ))
        )}

        {isTyping && statusText && (
          <div className="flex gap-3 animate-fadeIn">
            <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 bg-stone-200 text-black">
              <Bot size={16} />
            </div>
            <div className="px-4 py-2.5 rounded-2xl max-w-[80%] text-xs shadow-sm bg-white border border-stone-200 text-stone-600 rounded-tl-sm flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-stone-800" />
              <span className="font-medium">{statusText}</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-stone-100">
        <form
          onSubmit={handleSend}
          className="relative flex items-center max-w-4xl mx-auto"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your merchant assistant (e.g. 'Show order total received', 'Inspect customer chats')..."
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
