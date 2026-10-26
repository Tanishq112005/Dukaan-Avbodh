import { Bot, X, Maximize2, Minimize2, Plus } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatHeader({ isAiConnected, setIsAgentOpen, isFullScreen, setIsFullScreen, startNewChat }) {
  return (
    <div className="bg-stone-900 text-white flex-shrink-0">
      <div className={cn("flex items-center justify-between px-4 py-3 sm:py-3.5", isFullScreen ? "max-w-4xl mx-auto w-full" : "")}>
        <div className="flex items-center gap-2.5">
          <div className="bg-[#C45C26] p-1.5 rounded-full flex-shrink-0">
            <Bot size={16} className="text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-xs sm:text-sm tracking-tight text-white">Dukaan Atelier AI Stylist</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className={cn("w-1.5 h-1.5 rounded-full", isAiConnected ? "bg-emerald-400 animate-pulse" : "bg-red-400")} />
              <p className="text-[9px] sm:text-[10px] uppercase font-medium tracking-[0.14em] text-stone-400">
                {isAiConnected ? 'Online · Ready to style' : 'Reconnecting...'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            title="Start New Chat"
            onClick={startNewChat}
            className="text-stone-400 hover:text-white hover:bg-white/10 p-2 rounded-lg transition-colors cursor-pointer"
          >
            <Plus size={18} />
          </button>
          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="hidden sm:inline-flex text-stone-400 hover:text-white hover:bg-white/10 p-2 rounded-lg transition-colors cursor-pointer"
            title={isFullScreen ? "Minimize" : "Maximize"}
          >
            {isFullScreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button
            onClick={() => setIsAgentOpen(false)}
            className="text-stone-400 hover:text-white hover:bg-white/10 p-2 rounded-lg transition-colors cursor-pointer"
            title="Close chat"
          >
            <X size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
