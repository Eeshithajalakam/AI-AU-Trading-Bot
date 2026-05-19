"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { format } from "date-fns";
import { useTradingStore } from "@/store/useTradingStore";

export function MarketOverview() {
  const { currentPrice, priceHistory, isConnected } = useTradingStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || priceHistory.length === 0) {
    return (
      <Card className="col-span-full xl:col-span-8 flex items-center justify-center min-h-[450px]">
        <div className="flex flex-col items-center gap-4 text-slate-400">
          <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
          <p>Connecting to live data...</p>
        </div>
      </Card>
    );
  }

  const prevPrice = priceHistory[0]?.price || currentPrice;
  const change = currentPrice - prevPrice;
  const changePercent = prevPrice !== 0 ? (change / prevPrice) * 100 : 0;
  const isPositive = change >= 0;

  return (
    <Card className="col-span-full xl:col-span-8 relative overflow-hidden">
      {/* Realtime Status Indicator Glow */}
      <div className={`absolute -top-10 -right-10 w-40 h-40 blur-3xl opacity-20 pointer-events-none rounded-full transition-colors duration-1000 ${isConnected ? (isPositive ? 'bg-emerald-500' : 'bg-red-500') : 'bg-slate-500'}`} />
      
      <CardHeader className="flex flex-row items-center justify-between pb-2 relative z-10">
        <div className="space-y-1">
          <CardTitle className="text-xl flex items-center gap-3">
            XAU/USD (Gold)
            {isConnected ? (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                </span>
                LIVE
              </span>
            ) : (
              <span className="text-xs font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full border border-slate-700">
                OFFLINE
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className={`text-3xl font-bold tracking-tight text-white transition-colors duration-300 ${isPositive ? 'drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`}>
              ${currentPrice.toFixed(2)}
            </span>
            <span
              className={`text-sm font-medium ${
                isPositive ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {isPositive ? "+" : ""}
              {change.toFixed(2)} ({changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {["1M", "5M", "15M", "1H"].map((tf) => (
            <button
              key={tf}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                tf === "1M"
                  ? "bg-amber-500/20 text-amber-500 border border-amber-500/30"
                  : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="h-[350px] w-full mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={priceHistory} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                tickFormatter={(time) => {
                  try {
                    return format(new Date(time), "HH:mm:ss");
                  } catch {
                    return "";
                  }
                }}
                stroke="#52525b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                minTickGap={30}
              />
              <YAxis
                domain={['dataMin - 1', 'dataMax + 1']}
                stroke="#52525b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${value}`}
                orientation="right"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="glass rounded-lg p-3 border-white/10 shadow-xl">
                        <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                          {(() => {
                            try {
                              return format(new Date(payload[0].payload.time), "MMM dd, HH:mm:ss");
                            } catch {
                              return "";
                            }
                          })()}
                        </p>
                        <p className="text-lg font-bold text-white">
                          ${Number(payload[0].value).toFixed(2)}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={isPositive ? "#10b981" : "#ef4444"}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
                isAnimationActive={false} // Disable animation for real-time smoothness
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
