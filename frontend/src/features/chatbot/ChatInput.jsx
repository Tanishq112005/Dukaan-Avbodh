import { Send } from 'lucide-react';

export function ChatInput({ input, setInput, handleSend, isAiConnected }) {
  return (
    <form onSubmit={handleSend} className="p-3 bg-white border-t border-stone-100 flex items-center gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={!isAiConnected}
        placeholder="Ask for a look, size, or a better price..."
        className="flex-1 bg-[#FBF8F3] border border-stone-200 rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#C45C26]/25 focus:border-[#C45C26] transition-all placeholder:text-stone-400"
      />
      <button 
        type="submit" 
        disabled={!isAiConnected || !input.trim()}
        className="bg-stone-900 hover:bg-stone-800 disabled:opacity-50 text-white p-2.5 rounded-full shadow-sm transition-all flex-shrink-0"
      >
        <Send size={16} className="ml-0.5" />
      </button>
    </form>
  );
}
