import { Send } from 'lucide-react';

export function ChatInput({ input, setInput, handleSend, isAiConnected }) {
  return (
    <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-100 flex items-center gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={!isAiConnected}
        placeholder="Ask for a discount..."
        className="flex-1 bg-slate-50 border border-slate-200 rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
      />
      <button 
        type="submit" 
        disabled={!isAiConnected || !input.trim()}
        className="bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white p-2.5 rounded-full shadow-sm transition-all flex-shrink-0"
      >
        <Send size={16} className="ml-0.5" />
      </button>
    </form>
  );
}
