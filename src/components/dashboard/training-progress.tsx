"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Loader2, CheckCircle, XCircle } from "lucide-react";
import { useTradingStore } from "@/store/useTradingStore";
import { apiFetch } from "@/lib/api";

export function TrainingProgress() {
  const training = useTradingStore((s) => s.training);
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    apiFetch<{ metrics?: Record<string, unknown> }>("/api/training/metrics")
      .then((d) => setMetrics(d.metrics || null))
      .catch(() => {});
  }, [training?.status]);

  const isRunning = training?.status === "running" || training?.status === "starting";
  const isDone = training?.status === "completed";
  const isFailed = training?.status === "failed";

  return (
    <Card className="col-span-full xl:col-span-4">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-indigo-400" />
          <CardTitle className="text-base">AI Model Training</CardTitle>
        </div>
        {isRunning && <Loader2 className="h-4 w-4 animate-spin text-amber-400" />}
        {isDone && <CheckCircle className="h-4 w-4 text-emerald-400" />}
        {isFailed && <XCircle className="h-4 w-4 text-red-400" />}
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between text-xs text-slate-400">
          <span>{training?.status?.toUpperCase() || "IDLE"}</span>
          <span>{training?.progress_pct?.toFixed(0) ?? 0}%</span>
        </div>
        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${isFailed ? "bg-red-500" : isDone ? "bg-emerald-500" : "bg-indigo-500"}`}
            style={{ width: `${training?.progress_pct ?? 0}%` }}
          />
        </div>
        {training?.message && (
          <p className="text-xs text-slate-500 truncate">{training.message}</p>
        )}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-white/5 p-2">
            <p className="text-[10px] text-slate-500">MAE</p>
            <p className="text-sm font-semibold text-white">
              {String(training?.val_mae ?? metrics?.mae ?? "—")}
            </p>
          </div>
          <div className="rounded-lg bg-white/5 p-2">
            <p className="text-[10px] text-slate-500">RMSE</p>
            <p className="text-sm font-semibold text-white">
              {String(training?.val_rmse ?? metrics?.rmse ?? "—")}
            </p>
          </div>
          <div className="rounded-lg bg-white/5 p-2">
            <p className="text-[10px] text-slate-500">Dir. Acc</p>
            <p className="text-sm font-semibold text-emerald-400">
              {training?.directional_accuracy != null
                ? `${training.directional_accuracy}%`
                : metrics?.directional_accuracy != null
                ? `${metrics.directional_accuracy}%`
                : "—"}
            </p>
          </div>
        </div>
        {training?.current_epoch != null && training?.total_epochs ? (
          <p className="text-xs text-slate-500 text-center">
            Epoch {training.current_epoch} / {training.total_epochs}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
