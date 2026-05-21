"use client";

import { useEffect, useState } from "react";
import { Globe, AlertTriangle, Calendar, TrendingUp, TrendingDown, Minus, Activity } from "lucide-react";

interface MacroEvent {
  id: string;
  event: string;
  impact: string;
  asset_focus: string;
  time_offset_min: number;
}

interface MacroEnvironment {
  danger_zone: boolean;
  news_risk_score: number;
  active_high_impact_events: string[];
  macro_sentiment_score: number;
  macro_bias: string;
  calendar: MacroEvent[];
}

export function NewsTerminal() {
  const [env, setEnv] = useState<MacroEnvironment | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/news/macro");
        if (res.ok) {
          setEnv(await res.json());
        }
      } catch (err) {
        console.error("Failed to fetch macro environment");
      }
    };

    fetchNews();
    const interval = setInterval(fetchNews, 15000); // Check every 15s
    return () => clearInterval(interval);
  }, []);

  if (!env) return null;

  return (
    <div className="rounded-2xl border border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl p-6 xl:col-span-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Globe className="h-5 w-5 text-indigo-500" />
          Macro Intelligence
        </h2>
        
        {env.danger_zone ? (
          <div className="flex items-center gap-2 rounded-full bg-red-500/10 px-3 py-1 text-xs font-bold tracking-wider text-red-500 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.2)] animate-pulse">
            <AlertTriangle className="h-3 w-3" />
            TRADE HALT
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold tracking-wider text-emerald-500 border border-emerald-500/20">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            CLEAR TO TRADE
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="rounded-xl border border-white/5 bg-white/5 p-4 flex flex-col justify-between">
          <div className="text-sm text-slate-400 mb-1">XAU Sentiment</div>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{env.macro_sentiment_score.toFixed(1)}</div>
            {env.macro_bias.includes("BULL") ? <TrendingUp className="h-5 w-5 text-emerald-500" /> : 
             env.macro_bias.includes("BEAR") ? <TrendingDown className="h-5 w-5 text-red-500" /> : 
             <Minus className="h-5 w-5 text-slate-500" />}
          </div>
          <div className="mt-3 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 ${
                env.macro_bias.includes("BULL") ? "bg-emerald-500" : 
                env.macro_bias.includes("BEAR") ? "bg-red-500" : "bg-amber-500"
              }`}
              style={{ width: `${env.macro_sentiment_score}%` }}
            />
          </div>
        </div>

        <div className="rounded-xl border border-white/5 bg-white/5 p-4 flex flex-col justify-between">
          <div className="text-sm text-slate-400 mb-1">Macro Risk Score</div>
          <div className="flex items-center justify-between">
            <div className={`text-2xl font-bold ${
              env.news_risk_score > 80 ? "text-red-500" : 
              env.news_risk_score > 40 ? "text-amber-500" : "text-emerald-500"
            }`}>
              {env.news_risk_score}
            </div>
            <Activity className="h-5 w-5 text-slate-500" />
          </div>
          <div className="mt-3 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 shadow-[0_0_10px_currentColor] ${
                env.news_risk_score > 80 ? "bg-red-500 text-red-500" : 
                env.news_risk_score > 40 ? "bg-amber-500 text-amber-500" : "bg-emerald-500 text-emerald-500"
              }`}
              style={{ width: `${env.news_risk_score}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex-1">
        <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2 mb-3">
          <Calendar className="h-4 w-4" />
          Upcoming Events
        </h3>
        <div className="space-y-3">
          {env.calendar.filter(e => e.time_offset_min > -60).slice(0, 3).map((evt) => (
            <div key={evt.id} className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-3 hover:bg-white/5 transition-colors">
              <div className="flex flex-col">
                <span className="font-medium text-slate-200">{evt.event}</span>
                <span className="text-xs text-slate-500">{evt.asset_focus} • <span className={
                  evt.impact === "EXTREME" ? "text-red-400 font-semibold" : 
                  evt.impact === "HIGH" ? "text-amber-400 font-medium" : "text-slate-400"
                }>{evt.impact} IMPACT</span></span>
              </div>
              <div className={`text-sm font-medium ${
                evt.time_offset_min <= 15 && evt.time_offset_min > 0 ? "text-amber-500 animate-pulse" : 
                evt.time_offset_min <= 0 && evt.time_offset_min > -15 ? "text-red-500 animate-pulse" : "text-slate-400"
              }`}>
                {evt.time_offset_min <= 0 && evt.time_offset_min > -15 ? "LIVE" : 
                 evt.time_offset_min <= -15 ? "Ended" : 
                 `in ${Math.round(evt.time_offset_min)}m`}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
