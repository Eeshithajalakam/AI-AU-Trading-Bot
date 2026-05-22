"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, TrendingDown, Percent, DollarSign } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useTradingStore } from "@/store/useTradingStore";

interface Analytics {
  analytics: {
    total_signals: number;
    bullish_signals: number;
    bearish_signals: number;
    average_confidence: number;
  };
}

export function RiskMetrics() {
  const signals = useTradingStore((s) => s.signals);
  const currentPrice = useTradingStore((s) => s.currentPrice);
  const [analytics, setAnalytics] = useState<Analytics["analytics"] | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch<Analytics>("/api/analytics");
        setAnalytics(data.analytics);
      } catch { /* ignore */ }
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const winRate = analytics
    ? ((analytics.bullish_signals + analytics.bearish_signals) / Math.max(analytics.total_signals, 1) * 100).toFixed(1)
    : "—";
  const avgConf = analytics?.average_confidence?.toFixed(1) ?? "—";
  const latestConf = signals[0]?.confidence?.toFixed(0) ?? "—";

  const metrics = [
    { label: "AI Confidence", value: `${latestConf}%`, change: `avg ${avgConf}%`, isPositive: true, icon: Percent, color: "text-indigo-400", bg: "bg-indigo-500/10" },
    { label: "Signal Rate", value: `${winRate}%`, change: `${analytics?.total_signals ?? 0} total`, isPositive: true, icon: TrendingDown, color: "text-amber-400", bg: "bg-amber-500/10" },
    { label: "Bullish / Bearish", value: `${analytics?.bullish_signals ?? 0} / ${analytics?.bearish_signals ?? 0}`, change: "live", isPositive: true, icon: ShieldAlert, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: "Current Price", value: `$${currentPrice.toFixed(2)}`, change: "XAU/USD", isPositive: true, icon: DollarSign, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  ];

  return (
    <Card className="col-span-full xl:col-span-4">
      <CardHeader>
        <CardTitle>Risk Analytics</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg ${metric.bg}`}>
                <metric.icon className={`h-4 w-4 ${metric.color}`} />
              </div>
              <p className="text-xs font-medium text-slate-400">{metric.label}</p>
            </div>
            <div className="flex items-end justify-between">
              <p className="text-lg font-bold text-white">{metric.value}</p>
              <span className="text-xs font-medium text-slate-500">{metric.change}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
