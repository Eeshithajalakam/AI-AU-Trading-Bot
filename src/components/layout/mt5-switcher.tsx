"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert, Loader2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiFetch, getApiUrl } from "@/lib/api";

interface MT5Status {
  connected: boolean;
  account_mode: string;
  position_count?: number;
}

export function MT5Switcher() {
  const [status, setStatus] = useState<MT5Status | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiFetch<MT5Status>("/api/mt5/status");
        setStatus(data);
      } catch {
        setStatus({ connected: false, account_mode: "DEMO" });
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSwitch = async (mode: string) => {
    if (status?.account_mode === mode || loading) return;
    setLoading(true);
    try {
      const res = await fetch(getApiUrl("/api/mt5/switch-account"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Switched to ${mode} account`);
        setStatus((prev) => prev ? { ...prev, account_mode: mode, connected: data.connected } : null);
      } else {
        toast.error(data.detail || "Failed to switch account");
      }
    } catch {
      toast.error("Network error while switching account");
    } finally {
      setLoading(false);
    }
  };

  const isConnected = status?.connected;
  const isLive = status?.account_mode === "LIVE";

  return (
    <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1 backdrop-blur-md">
      <button
        disabled={loading}
        className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
          !isLive ? "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30" : "text-slate-400 hover:bg-white/5"
        }`}
        onClick={() => handleSwitch("DEMO")}
      >
        DEMO
      </button>
      <button
        disabled={loading}
        className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
          isLive ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "text-slate-400 hover:bg-white/5"
        }`}
        onClick={() => handleSwitch("LIVE")}
      >
        LIVE
      </button>
      <div className="h-4 w-px bg-white/10 mx-1" />
      {loading ? (
        <Loader2 className="h-4 w-4 text-slate-400 animate-spin pr-2" />
      ) : isConnected ? (
        <ShieldCheck className="h-4 w-4 text-emerald-500 pr-2" />
      ) : (
        <ShieldAlert className="h-4 w-4 text-red-500 pr-2" />
      )}
    </div>
  );
}
