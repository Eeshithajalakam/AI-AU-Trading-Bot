"use client";

import { useState, useEffect } from "react";
import { X, ShieldAlert, Save, Activity, Settings2, Power } from "lucide-react";
import { toast } from "react-hot-toast";

interface RiskSettings {
  max_daily_drawdown_pct: number;
  max_trade_risk_pct: number;
  max_daily_trades: number;
  emergency_shutdown: boolean;
}

export function RiskSettingsModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [settings, setSettings] = useState<RiskSettings>({
    max_daily_drawdown_pct: 5.0,
    max_trade_risk_pct: 2.0,
    max_daily_trades: 15,
    emergency_shutdown: false
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const { getApiUrl } = await import("@/lib/api");
      const res = await fetch(getApiUrl("/api/settings/risk"));
      if (res.ok) {
        setSettings(await res.json());
      }
    } catch (err) {
      toast.error("Failed to load risk settings");
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const { getApiUrl } = await import("@/lib/api");
      const res = await fetch(getApiUrl("/api/settings/risk"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message, {
          style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(16, 185, 129, 0.2)' }
        });
        onClose();
      } else {
        toast.error(data.detail || "Failed to save settings");
      }
    } catch (err) {
      toast.error("Network error while saving settings");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative w-full max-w-lg rounded-2xl border border-white/10 bg-[#0a0a0c] p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500/10 border border-indigo-500/20">
              <Settings2 className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Risk Control Center</h2>
              <p className="text-xs text-slate-400">Manage institutional safeguards</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-full p-2 text-slate-400 hover:bg-white/10 transition-colors">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          </div>
        ) : (
          <div className="space-y-6 py-6">
            
            {/* Global Kill Switch */}
            <div className={`flex items-center justify-between rounded-xl border p-4 transition-colors ${
              settings.emergency_shutdown 
                ? "border-red-500/50 bg-red-500/10" 
                : "border-white/5 bg-white/5"
            }`}>
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  settings.emergency_shutdown ? "bg-red-500/20 text-red-500" : "bg-white/10 text-slate-400"
                }`}>
                  <Power className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-medium text-white">Emergency Kill Switch</h3>
                  <p className="text-xs text-slate-400">Instantly halt all automated trading</p>
                </div>
              </div>
              <button 
                onClick={() => setSettings(s => ({ ...s, emergency_shutdown: !s.emergency_shutdown }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.emergency_shutdown ? "bg-red-500" : "bg-slate-700"
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.emergency_shutdown ? "translate-x-6" : "translate-x-1"
                }`} />
              </button>
            </div>

            {/* Sliders */}
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm font-medium text-slate-300">Max Daily Drawdown</label>
                  <span className="text-sm font-bold text-amber-500">{settings.max_daily_drawdown_pct}%</span>
                </div>
                <input 
                  type="range" min="0.5" max="20" step="0.5"
                  value={settings.max_daily_drawdown_pct}
                  onChange={(e) => setSettings(s => ({...s, max_daily_drawdown_pct: parseFloat(e.target.value)}))}
                  className="w-full accent-amber-500"
                />
                <p className="text-xs text-slate-500 mt-1">Stops trading if account drops this percentage in 24h.</p>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm font-medium text-slate-300">Max Risk per Trade</label>
                  <span className="text-sm font-bold text-indigo-400">{settings.max_trade_risk_pct}%</span>
                </div>
                <input 
                  type="range" min="0.5" max="10" step="0.1"
                  value={settings.max_trade_risk_pct}
                  onChange={(e) => setSettings(s => ({...s, max_trade_risk_pct: parseFloat(e.target.value)}))}
                  className="w-full accent-indigo-500"
                />
                <p className="text-xs text-slate-500 mt-1">Position sizing adjusted by AI confidence & ATR.</p>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-sm font-medium text-slate-300">Max Daily Trades</label>
                  <span className="text-sm font-bold text-emerald-400">{settings.max_daily_trades}</span>
                </div>
                <input 
                  type="range" min="1" max="50" step="1"
                  value={settings.max_daily_trades}
                  onChange={(e) => setSettings(s => ({...s, max_daily_trades: parseInt(e.target.value)}))}
                  className="w-full accent-emerald-500"
                />
                <p className="text-xs text-slate-500 mt-1">Prevents over-trading during volatile chop.</p>
              </div>
            </div>

          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-white/10 pt-4">
          <button 
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={saveSettings}
            disabled={saving || loading}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {saving ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" /> : <Save className="h-4 w-4" />}
            Save Parameters
          </button>
        </div>
      </div>
    </div>
  );
}
