import { Bot, X, Maximize2, Minimize2 } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatHeader({ isAiConnected, setIsAgentOpen, isFullScreen, setIsFullScreen }) {
  return (
    <div className="flex items-center justify-between px-4 py-3.5 bg-stone-900 text-white">
      <div className="flex items-center gap-2.5">
        <div className="bg-[#C45C26] p-1.5 rounded-full"><Bot size={18} className="text-white" /></div>
        <div>
          <h3 className="font-semibold text-sm tracking-tight">Dukkan Stylist</h3>
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className={cn("w-1.5 h-1.5 rounded-full", isAiConnected ? "bg-emerald-400" : "bg-red-400")} />
            <p className="text-[10px] uppercase font-medium tracking-[0.14em] text-stone-400">
              {isAiConnected ? 'Online · ready to style' : 'Offline'}
            </p>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <button onClick={() => setIsFullScreen(!isFullScreen)} className="text-stone-400 hover:text-white hover:bg-white/10 p-1.5 rounded-md transition-colors">
          {isFullScreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
        <button onClick={() => setIsAgentOpen(false)} className="text-stone-400 hover:text-white hover:bg-white/10 p-1.5 rounded-md transition-colors">
          <X size={18} />
        </button>
      </div>
    </div>
  );
}
