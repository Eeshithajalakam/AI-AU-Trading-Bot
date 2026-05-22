"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, ArrowUpRight, ArrowDownRight, Target, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTradingStore } from "@/store/useTradingStore";

export function AISignals() {
  const { signals, isConnected } = useTradingStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || signals.length === 0) {
    return (
      <Card className="flex flex-col min-h-[200px]">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-indigo-500/10 p-2 border border-indigo-500/20">
              <Brain className="h-4 w-4 text-indigo-400" />
            </div>
            <CardTitle>AI Predictions</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-slate-400 text-sm animate-pulse">Waiting for signals...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col relative overflow-hidden min-h-[220px]">
      <CardHeader className="flex flex-row items-center justify-between relative z-10">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-indigo-500/10 p-2 border border-indigo-500/20">
            <Brain className="h-4 w-4 text-indigo-400" />
          </div>
          <CardTitle>AI Predictions</CardTitle>
        </div>
        <Badge variant="outline" className={`${isConnected ? 'animate-pulse border-indigo-500/30 text-indigo-400 bg-indigo-500/10' : 'border-slate-700 text-slate-500 bg-slate-800'}`}>
          {isConnected ? 'Live Analysis' : 'Offline'}
        </Badge>
      </CardHeader>
      <CardContent className="flex-1 space-y-4 relative z-10">
        <AnimatePresence>
          {signals.map((signal, i) => (
            <motion.div
              key={signal.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: i * 0.1 }}
              className={`relative overflow-hidden rounded-xl border p-4 ${
                signal.active
                  ? "bg-gradient-to-br from-white/5 to-white-[0.02] border-white/10"
                  : "bg-white/[0.02] border-white/5 opacity-70"
              }`}
            >
              {signal.active && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none" />
              )}
              
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Badge variant={signal.type === "LONG" ? "success" : "destructive"}>
                    {signal.type === "LONG" ? (
                      <ArrowUpRight className="mr-1 h-3 w-3" />
                    ) : (
                      <ArrowDownRight className="mr-1 h-3 w-3" />
                    )}
                    {signal.type}
                  </Badge>
                  <span className="text-sm font-medium text-slate-300">{signal.asset}</span>
                </div>
                <span className="text-xs text-slate-500">
                  {new Date(signal.timestamp).toLocaleTimeString()}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Entry Range</p>
                  <p className="text-sm font-semibold text-white">${signal.entry.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <Target className="h-3 w-3 text-emerald-400" /> Target
                  </p>
                  <p className="text-sm font-semibold text-emerald-400">${signal.target.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Confidence</p>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-500 rounded-full transition-all duration-1000"
                        style={{ width: `${signal.confidence}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-indigo-400">{signal.confidence}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3 text-red-400" /> Stop Loss
                  </p>
                  <p className="text-sm font-semibold text-red-400">${signal.stopLoss.toFixed(2)}</p>
                </div>
              </div>
              
              {signal.active && (
                <button className="w-full mt-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 py-2 text-xs font-medium text-white transition-colors relative overflow-hidden group">
                  <span className="relative z-10">Execute Trade</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-amber-500/0 via-amber-500/10 to-amber-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                </button>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
