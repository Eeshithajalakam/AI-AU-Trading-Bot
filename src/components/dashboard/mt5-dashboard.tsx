"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Wallet, TrendingUp, Shield, Activity } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useTradingStore } from "@/store/useTradingStore";

interface MT5Dashboard {
  account: {
    balance?: number;
    equity?: number;
    profit?: number;
    margin?: number;
    paper?: boolean;
  };
  positions: Array<{
    ticket: number;
    symbol: string;
    type: string;
    volume: number;
    profit: number;
    open_price: number;
  }>;
  position_count: number;
  paper_mode: boolean;
  auto_trade: boolean;
  daily_pnl: number;
}

export function MT5Dashboard() {
  const risk = useTradingStore((s) => s.risk);
  const [data, setData] = useState<MT5Dashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setData(await apiFetch<MT5Dashboard>("/api/mt5/account"));
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, []);

  const account = data?.account || risk?.account;
  const balance = account?.balance ?? 10000;
  const equity = account?.equity ?? balance;
  const profit = account?.profit ?? risk?.daily_pnl ?? 0;

  return (
    <Card className="col-span-full xl:col-span-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Wallet className="h-4 w-4 text-amber-400" />
          MT5 Account
          {data?.paper_mode && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
              PAPER
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-24 flex items-center justify-center text-slate-500 text-sm">Loading account...</div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1"><Wallet className="h-3 w-3" /> Balance</p>
                <p className="text-lg font-bold text-white">${balance.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1"><TrendingUp className="h-3 w-3" /> Equity</p>
                <p className="text-lg font-bold text-white">${equity.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <p className="text-xs text-slate-500">Floating P/L</p>
                <p className={`text-lg font-bold ${profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {profit >= 0 ? "+" : ""}${profit.toFixed(2)}
                </p>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <p className="text-xs text-slate-500 flex items-center gap-1"><Activity className="h-3 w-3" /> Open</p>
                <p className="text-lg font-bold text-white">{data?.position_count ?? 0}</p>
              </div>
            </div>
            {data?.auto_trade && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
                <Shield className="h-3 w-3" /> Auto-trading enabled
              </div>
            )}
            {data?.positions && data.positions.length > 0 && (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {data.positions.map((p) => (
                  <div key={p.ticket} className="flex justify-between text-xs py-1 border-b border-white/5">
                    <span className={p.type === "BUY" ? "text-emerald-400" : "text-red-400"}>{p.type} {p.symbol}</span>
                    <span className={p.profit >= 0 ? "text-emerald-400" : "text-red-400"}>${p.profit.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
