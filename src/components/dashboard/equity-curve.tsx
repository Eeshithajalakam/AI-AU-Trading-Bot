"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import { apiFetch } from "@/lib/api";

export function EquityCurve() {
  const [data, setData] = useState<{ equity: number; index: number }[]>([]);
  const [netPnl, setNetPnl] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiFetch<{ equity_curve: number[]; net_pnl: number }>("/api/performance/equity-curve");
        setData(res.equity_curve.map((v, i) => ({ equity: v, index: i })));
        setNetPnl(res.net_pnl ?? 0);
      } catch {
        setData([]);
      } finally {
        setLoading(false);
      }
    };
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, []);

  const positive = netPnl >= 0;

  return (
    <Card className="col-span-full xl:col-span-8">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className={`h-4 w-4 ${positive ? "text-emerald-400" : "text-red-400"}`} />
          Equity Curve
        </CardTitle>
        <span className={`text-sm font-semibold ${positive ? "text-emerald-400" : "text-red-400"}`}>
          {positive ? "+" : ""}${netPnl.toFixed(2)} net
        </span>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-[200px] flex items-center justify-center text-slate-500 text-sm">Loading...</div>
        ) : data.length < 2 ? (
          <div className="h-[200px] flex items-center justify-center text-slate-500 text-sm">
            Execute trades to build equity history
          </div>
        ) : (
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={positive ? "#10b981" : "#ef4444"} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={positive ? "#10b981" : "#ef4444"} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="index" hide />
                <YAxis domain={["auto", "auto"]} tickFormatter={(v) => `$${v}`} stroke="#64748b" fontSize={11} width={55} />
                <Tooltip
                  content={({ payload }) =>
                    payload?.[0] ? (
                      <div className="glass rounded p-2 text-sm border border-white/10">
                        ${Number(payload[0].value).toFixed(2)}
                      </div>
                    ) : null
                  }
                />
                <Area type="monotone" dataKey="equity" stroke={positive ? "#10b981" : "#ef4444"} fill="url(#eqGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
