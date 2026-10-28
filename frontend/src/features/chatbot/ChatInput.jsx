import { Send, Sparkles, Tag, Ruler, Package } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatInput({ input, setInput, handleSend, isAiConnected, isFullScreen, onQuickPrompt }) {
  const quickChips = [
    { label: "Style Look", prompt: "Curate a luxury outfit pairing for this weekend." },
    { label: "VIP Bargain", prompt: "Can you offer me a VIP discount on items in my cart?" },
    { label: "Fit & Size", prompt: "How do your sizes fit? Give me size recommendations." },
    { label: "Track Orders", prompt: "What is the status of my recent orders?" },
  ];

  return (
    <div className={cn(isFullScreen ? "p-4 sm:p-6 pb-[max(1rem,env(safe-area-inset-bottom))] bg-[#FBF8F3] border-t border-stone-200/80" : "p-3 pb-[max(0.875rem,env(safe-area-inset-bottom))] bg-white border-t border-stone-100")}>
      <div className={cn("space-y-2", isFullScreen ? "max-w-2xl mx-auto w-full" : "")}>
        {/* Quick Suggestion Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-hide">
          {quickChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onQuickPrompt?.(chip.prompt)}
              className="flex-shrink-0 text-[11px] font-medium text-stone-600 hover:text-stone-900 bg-stone-100 hover:bg-stone-200/80 border border-stone-200/60 rounded-full px-2.5 py-1 transition-all cursor-pointer whitespace-nowrap"
            >
              {chip.label}
            </button>
          ))}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!isAiConnected}
            placeholder="Ask for looks, sizes, or VIP discount..."
            // text-base on mobile prevents iOS Safari from auto-zooming the viewport
            className="flex-1 bg-[#FBF8F3] border border-stone-200/90 rounded-full px-4 sm:px-5 py-2.5 sm:py-3 text-base sm:text-sm outline-none focus:ring-2 focus:ring-[#C45C26]/20 focus:border-[#C45C26] transition-all placeholder:text-stone-400"
          />
          <button 
            type="submit" 
            disabled={!isAiConnected || !input.trim()}
            className="bg-stone-900 hover:bg-[#6e1423] disabled:opacity-50 text-white p-2.5 sm:p-3 rounded-full shadow-xs transition-all flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
            title="Send message"
          >
            <Send size={15} className="ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
