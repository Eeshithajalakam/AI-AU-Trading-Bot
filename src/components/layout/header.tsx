"use client";

import { useState } from "react";
import { Bell, Search, Zap, Settings as SettingsIcon } from "lucide-react";
import { MT5Switcher } from "./mt5-switcher";
import { RiskSettingsModal } from "../dashboard/risk-settings-modal";

export function Header() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-white/5 bg-[#0a0a0c]/80 px-6 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-md">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs font-medium text-slate-300">XAU/USD Market Open</span>
        </div>
        <div className="h-4 w-px bg-white/10" />
        <MT5Switcher />
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-amber-500 transition-colors" />
          <input
            type="text"
            placeholder="Search markets..."
            className="h-9 w-64 rounded-full border border-white/10 bg-white/5 pl-9 pr-4 text-sm text-white placeholder:text-slate-500 focus:border-amber-500/50 focus:outline-none focus:ring-1 focus:ring-amber-500/50 transition-all"
          />
        </div>
        
        <button className="relative rounded-full p-2 text-slate-400 hover:bg-white/10 hover:text-white transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 flex h-2 w-2 rounded-full bg-amber-500">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75"></span>
          </span>
        </button>
        
        <button 
          onClick={() => setIsSettingsOpen(true)}
          className="relative rounded-full p-2 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
        >
          <SettingsIcon className="h-5 w-5" />
        </button>
        
        <button className="flex items-center gap-2 rounded-full bg-amber-500/10 px-4 py-2 text-sm font-medium text-amber-500 hover:bg-amber-500/20 transition-colors border border-amber-500/20">
          <Zap className="h-4 w-4" />
          Auto-Trade Active
        </button>
      </div>
      
      <RiskSettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </header>
  );
}
