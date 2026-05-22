"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useTradingStore } from "@/store/useTradingStore";

export function PnlTracker() {
  const risk = useTradingStore((s) => s.risk);
  const [pnl, setPnl] = useState<{ daily_pnl: number; open_trades: number } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setPnl(await apiFetch("/api/trades/pnl"));
      } catch { /* ignore */ }
    };
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  const daily = risk?.daily_pnl ?? pnl?.daily_pnl ?? 0;
  const isPositive = daily >= 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <DollarSign className={`h-4 w-4 ${isPositive ? "text-emerald-400" : "text-red-400"}`} />
          Live P&L (24h)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className={`text-2xl font-bold ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
          {isPositive ? "+" : ""}${Math.abs(daily).toFixed(2)}
        </p>
        <p className="text-xs text-slate-500 mt-1">{pnl?.open_trades ?? 0} open positions</p>
      </CardContent>
    </Card>
  );
}
