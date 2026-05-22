"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

interface TradeLog {
  signal_id?: string;
  status: string;
  timestamp: string;
  details?: { price?: number; volume?: number };
  risk_profile?: { volume?: number };
}

export function TradeHistory() {
  const [trades, setTrades] = useState<TradeLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch<TradeLog[]>("/api/trades/history?limit=20");
        setTrades(data);
      } catch {
        setTrades([]);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="col-span-full xl:col-span-8">
      <CardHeader>
        <CardTitle>Trade Journal</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex h-32 items-center justify-center text-slate-400 text-sm">Loading trades...</div>
        ) : trades.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-slate-500 text-sm">
            No trades yet. Enable auto-trade or execute via MT5.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-slate-300">
              <thead className="text-xs uppercase bg-white/5 text-slate-400">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Signal</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Volume</th>
                  <th className="px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, i) => (
                  <tr key={`${trade.timestamp}-${i}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="px-4 py-3 font-medium text-slate-400">{trade.signal_id || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`font-semibold ${
                        trade.status === "EXECUTED" ? "text-emerald-400" :
                        trade.status.includes("BLOCKED") ? "text-amber-400" : "text-red-400"
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {trade.risk_profile?.volume?.toFixed(2) || trade.details?.volume || "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
