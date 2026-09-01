import { Bot, X } from 'lucide-react';
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) { return twMerge(clsx(inputs)); }

export function ChatHeader({ isAiConnected, setIsAgentOpen }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
      <div className="flex items-center gap-2">
        <div className="bg-indigo-100 p-1.5 rounded-full"><Bot size={18} className="text-indigo-600" /></div>
        <div>
          <h3 className="font-semibold text-slate-800 text-sm">Dukkan AI Agent</h3>
          <div className="flex items-center gap-1.5 mt-0.5">
            <div className={cn("w-2 h-2 rounded-full", isAiConnected ? "bg-green-500" : "bg-red-500")} />
            <p className="text-[10px] uppercase font-medium tracking-wide text-slate-500">{isAiConnected ? 'Online (Proactive)' : 'Offline'}</p>
          </div>
        </div>
      </div>
      <button onClick={() => setIsAgentOpen(false)} className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-md transition-colors">
        <X size={18} />
      </button>
    </div>
  );
}
