"use client";

import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Play, TrendingUp, TrendingDown, Target, Activity, ShieldAlert, DollarSign } from "lucide-react";
import { toast } from "react-hot-toast";

interface BacktestReport {
  summary: {
    initial_capital: number;
    final_capital: number;
    net_profit: number;
    roi_pct: number;
    total_trades: number;
    win_rate_pct: number;
    profit_factor: number;
  };
  metrics: {
    sharpe_ratio: number;
    max_drawdown_pct: number;
    average_win_usd: number;
    average_loss_usd: number;
  };
  equity_curve: number[];
  recent_trades: any[];
}

export function BacktestEngineUI() {
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);
  const [capital, setCapital] = useState(10000);
  const [report, setReport] = useState<BacktestReport | null>(null);

  const runBacktest = async () => {
    setLoading(true);
    setReport(null);
    try {
      const res = await fetch(`http://localhost:8000/api/backtest/run?days=${days}&capital=${capital}`, {
        method: "POST"
      });
      const data = await res.json();
      
      if (res.ok && !data.error) {
        setReport(data);
        toast.success("Historical replay completed", {
          style: { background: '#1f1f23', color: '#ededed', border: '1px solid rgba(16, 185, 129, 0.2)' }
        });
      } else {
        toast.error(data.error || "Failed to run backtest");
      }
    } catch (err) {
      toast.error("Network error executing backtest");
    } finally {
      setLoading(false);
    }
  };

  const chartData = report?.equity_curve.map((val, idx) => ({
    step: idx,
    capital: val
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 rounded-2xl border border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl p-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Activity className="h-6 w-6 text-indigo-500" />
            Strategy Backtester
          </h1>
          <p className="text-slate-400 text-sm mt-1">Run high-speed historical replay simulations</p>
        </div>
        
        <div className="flex items-center gap-4 bg-white/5 p-2 rounded-xl border border-white/5">
          <div className="flex flex-col px-2">
            <label className="text-xs text-slate-500 mb-1">Timeframe (Days)</label>
            <input 
              type="number" 
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-20 bg-transparent border-b border-white/10 text-white focus:outline-none focus:border-indigo-500 text-sm"
            />
          </div>
          <div className="w-px h-8 bg-white/10" />
          <div className="flex flex-col px-2">
            <label className="text-xs text-slate-500 mb-1">Capital ($)</label>
            <input 
              type="number" 
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="w-24 bg-transparent border-b border-white/10 text-white focus:outline-none focus:border-indigo-500 text-sm"
            />
          </div>
          
          <button 
            onClick={runBacktest}
            disabled={loading}
            className="ml-2 flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-bold text-white hover:bg-indigo-700 transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(79,70,229,0.3)]"
          >
            {loading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Play className="h-4 w-4 fill-current" />
            )}
            Run Simulation
          </button>
        </div>
      </div>

      {/* Results */}
      {report && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          
          {/* Main Chart */}
          <div className="xl:col-span-2 rounded-2xl border border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl p-6 flex flex-col min-h-[400px]">
            <h2 className="text-lg font-semibold mb-4 text-white">Equity Curve</h2>
            <div className="flex-1 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCapital" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="step" hide />
                  <YAxis 
                    domain={['dataMin - 100', 'auto']} 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{fill: '#64748b', fontSize: 12}} 
                    tickFormatter={(val) => `$${val.toLocaleString()}`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Equity']}
                    labelFormatter={() => ''}
                  />
                  <Area type="monotone" dataKey="capital" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorCapital)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Metrics Panel */}
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-white/5 bg-white/5 p-4">
                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1"><DollarSign className="h-3 w-3"/> Net Profit</div>
                <div className={`text-xl font-bold ${report.summary.net_profit >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                  ${report.summary.net_profit.toLocaleString()}
                </div>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-4">
                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1"><TrendingUp className="h-3 w-3"/> ROI</div>
                <div className={`text-xl font-bold ${report.summary.roi_pct >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                  {report.summary.roi_pct}%
                </div>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-4">
                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1"><Target className="h-3 w-3"/> Win Rate</div>
                <div className="text-xl font-bold text-white">{report.summary.win_rate_pct}%</div>
              </div>
              <div className="rounded-xl border border-white/5 bg-white/5 p-4">
                <div className="text-slate-400 text-xs mb-1 flex items-center gap-1"><Activity className="h-3 w-3"/> Trades</div>
                <div className="text-xl font-bold text-white">{report.summary.total_trades}</div>
              </div>
            </div>

            <div className="rounded-xl border border-white/5 bg-white/5 p-5 space-y-4">
              <h3 className="font-semibold text-white border-b border-white/10 pb-2">Quantitative Metrics</h3>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Sharpe Ratio</span>
                <span className={`font-bold ${report.metrics.sharpe_ratio >= 1.5 ? "text-emerald-400" : "text-amber-400"}`}>
                  {report.metrics.sharpe_ratio}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400 flex items-center gap-1"><ShieldAlert className="h-3 w-3"/> Max Drawdown</span>
                <span className="font-bold text-red-400">{report.metrics.max_drawdown_pct}%</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Profit Factor</span>
                <span className="font-bold text-white">{report.summary.profit_factor}</span>
              </div>
              
              <div className="flex justify-between items-center border-t border-white/5 pt-2">
                <span className="text-sm text-slate-400">Avg Win</span>
                <span className="font-bold text-emerald-500">${report.metrics.average_win_usd}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Avg Loss</span>
                <span className="font-bold text-red-500">-${report.metrics.average_loss_usd}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
