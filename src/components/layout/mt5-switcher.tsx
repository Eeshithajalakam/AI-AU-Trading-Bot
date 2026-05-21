"use client";

import { useEffect, useState } from "react";
import { Server, ShieldCheck, ShieldAlert, Loader2 } from "lucide-react";
import { toast } from "react-hot-toast";

interface MT5Status {
  status: string;
  account_type: string;
  total_active_trades?: number;
}

export function MT5Switcher() {
  const [status, setStatus] = useState<MT5Status | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/mt5/status");
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
        }
      } catch (err) {
        console.error("Failed to fetch MT5 status", err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleSwitch = async (type: string) => {
    if (status?.account_type === type || loading) return;
    
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/mt5/switch-account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_type: type })
      });
      
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message, {
          style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(16, 185, 129, 0.2)' }
        });
        setStatus(prev => prev ? { ...prev, account_type: type, status: "connected" } : null);
      } else {
        toast.error(data.detail || "Failed to switch account", {
          style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(239, 68, 68, 0.2)' }
        });
      }
    } catch (err) {
      toast.error("Network error while switching account");
    } finally {
      setLoading(false);
    }
  };

  const isConnected = status?.status === "connected";
  const isLive = status?.account_type === "LIVE";

  return (
    <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1 backdrop-blur-md">
      <button 
        disabled={loading}
        className={`flex items-center justify-center px-3 py-1 rounded-full text-xs font-medium transition-all ${
          !isLive 
            ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 shadow-[0_0_10px_rgba(99,102,241,0.2)]" 
            : "text-slate-400 hover:text-slate-300 hover:bg-white/5 border border-transparent"
        }`}
        onClick={() => handleSwitch("DEMO")}
      >
        DEMO
      </button>
      
      <button 
        disabled={loading}
        className={`flex items-center justify-center px-3 py-1 rounded-full text-xs font-medium transition-all ${
          isLive 
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]" 
            : "text-slate-400 hover:text-slate-300 hover:bg-white/5 border border-transparent"
        }`}
        onClick={() => handleSwitch("LIVE")}
      >
        LIVE
      </button>
      
      <div className="h-4 w-px bg-white/10 mx-1" />
      
      <div className="pr-2 pl-1 flex items-center gap-2 group relative">
        {loading ? (
          <Loader2 className="h-4 w-4 text-slate-400 animate-spin" />
        ) : isConnected ? (
          <>
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span className="absolute top-8 left-1/2 -translate-x-1/2 w-max px-2 py-1 bg-slate-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              MT5 Connected
            </span>
          </>
        ) : (
          <>
            <ShieldAlert className="h-4 w-4 text-red-500" />
            <span className="absolute top-8 left-1/2 -translate-x-1/2 w-max px-2 py-1 bg-slate-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              MT5 Disconnected
            </span>
          </>
        )}
      </div>
    </div>
  );
}
