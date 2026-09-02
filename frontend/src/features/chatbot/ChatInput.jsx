import { Send } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatInput({ input, setInput, handleSend, isAiConnected, isFullScreen }) {
  return (
    <div className={cn(isFullScreen ? "p-6 bg-[#FBF8F3]" : "p-3 bg-white border-t border-stone-100")}>
      <form onSubmit={handleSend} className={cn("flex items-center gap-2", isFullScreen ? "max-w-2xl mx-auto w-full" : "")}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={!isAiConnected}
          placeholder="Ask for a look, size, or a better price..."
          className="flex-1 bg-[#FBF8F3] border border-stone-200 rounded-full px-5 py-3 text-sm outline-none focus:ring-2 focus:ring-[#C45C26]/25 focus:border-[#C45C26] transition-all placeholder:text-stone-400"
        />
        <button 
          type="submit" 
          disabled={!isAiConnected || !input.trim()}
          className="bg-stone-900 hover:bg-stone-800 disabled:opacity-50 text-white p-3 rounded-full shadow-sm transition-all flex-shrink-0"
        >
          <Send size={18} className="ml-0.5" />
        </button>
      </form>
    </div>
  );
}
