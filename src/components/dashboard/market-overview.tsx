"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTradingStore } from "@/store/useTradingStore";
import { CandlestickChart } from "./candlestick-chart";

export function MarketOverview() {
  const { currentPrice, priceHistory, candles, isConnected } = useTradingStore();
  const [mounted, setMounted] = useState(false);
  const [chartMode, setChartMode] = useState<"candle" | "line">("candle");

  useEffect(() => setMounted(true), []);

  if (!mounted || (priceHistory.length === 0 && candles.length === 0)) {
    return (
      <Card className="col-span-full xl:col-span-8 flex items-center justify-center min-h-[450px]">
        <div className="flex flex-col items-center gap-4 text-slate-400">
          <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <p>Connecting to live XAU/USD feed...</p>
        </div>
      </Card>
    );
  }

  const prevPrice = priceHistory[0]?.price || currentPrice;
  const change = currentPrice - prevPrice;
  const changePercent = prevPrice !== 0 ? (change / prevPrice) * 100 : 0;
  const isPositive = change >= 0;

  return (
    <Card className="col-span-full xl:col-span-8 relative overflow-hidden min-h-[450px]">
      <div className={`absolute -top-10 -right-10 w-40 h-40 blur-3xl opacity-20 pointer-events-none rounded-full ${isConnected ? (isPositive ? "bg-emerald-500" : "bg-red-500") : "bg-slate-500"}`} />

      <CardHeader className="flex flex-row items-center justify-between pb-2 relative z-10">
        <div className="space-y-1">
          <CardTitle className="text-xl flex items-center gap-3">
            XAU/USD (Gold)
            {isConnected ? (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                </span>
                LIVE
              </span>
            ) : (
              <span className="text-xs font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full border border-slate-700">OFFLINE</span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">${currentPrice.toFixed(2)}</span>
            <span className={`text-sm font-medium ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
              {isPositive ? "+" : ""}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {(["candle", "line"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setChartMode(mode)}
              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                chartMode === mode ? "bg-amber-500/20 text-amber-500 border border-amber-500/30" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {mode === "candle" ? "Candles" : "Line"}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="h-[350px] w-full mt-2">
          {chartMode === "candle" && candles.length > 0 ? (
            <CandlestickChart height={350} />
          ) : (
            <div className="flex h-full items-center justify-center text-slate-500 text-sm">
              {candles.length === 0 ? "Building candle data..." : "Switch to Candles view"}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
