"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert, TrendingDown, Percent, DollarSign } from "lucide-react";

export function RiskMetrics() {
  const metrics = [
    {
      label: "Win Rate",
      value: "68.4%",
      change: "+2.1%",
      isPositive: true,
      icon: Percent,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
    },
    {
      label: "Max Drawdown",
      value: "4.2%",
      change: "-0.5%",
      isPositive: true,
      icon: TrendingDown,
      color: "text-red-400",
      bg: "bg-red-500/10",
    },
    {
      label: "Risk/Reward",
      value: "1:2.4",
      change: "+0.2",
      isPositive: true,
      icon: ShieldAlert,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      label: "Daily P&L",
      value: "$1,666.30",
      change: "+12.4%",
      isPositive: true,
      icon: DollarSign,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
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
              <span className={`text-xs font-medium ${metric.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {metric.change}
              </span>
            </div>
          </div>
        ))}
        <div className="col-span-2 mt-2">
          <div className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-500/5 flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-indigo-400 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-white">Risk Level: Low</p>
              <p className="text-xs text-slate-400 mt-1">
                Current exposure is well within predefined limits. Auto-hedging is active.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
