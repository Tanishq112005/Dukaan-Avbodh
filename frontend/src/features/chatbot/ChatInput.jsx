import { Send } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatInput({ input, setInput, handleSend, isAiConnected, isFullScreen }) {
  return (
    <div className={cn(isFullScreen ? "p-4 sm:p-6 bg-[#FBF8F3]" : "p-3 pb-4 sm:pb-3 bg-white border-t border-stone-100")}>
      <form onSubmit={handleSend} className={cn("flex items-center gap-2", isFullScreen ? "max-w-2xl mx-auto w-full" : "")}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!isAiConnected}
          placeholder="Ask for looks, sizes, or VIP discount..."
          // text-base on mobile prevents iOS Safari from auto-zooming the viewport
          className="flex-1 bg-[#FBF8F3] border border-stone-200 rounded-full px-4 sm:px-5 py-2.5 sm:py-3 text-base sm:text-sm outline-none focus:ring-2 focus:ring-[#C45C26]/25 focus:border-[#C45C26] transition-all placeholder:text-stone-400"
        />
        <button 
          type="submit" 
          disabled={!isAiConnected || !input.trim()}
          className="bg-stone-900 hover:bg-[#6e1423] disabled:opacity-50 text-white p-2.5 sm:p-3 rounded-full shadow-sm transition-all flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
          title="Send message"
        >
          <Send size={16} className="ml-0.5" />
        </button>
      </form>
    </div>
  );
}
