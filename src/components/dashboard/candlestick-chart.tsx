"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, Time } from "lightweight-charts";
import { useTradingStore, CandlePoint } from "@/store/useTradingStore";

function toChartTime(iso: string): Time {
  return Math.floor(new Date(iso).getTime() / 1000) as Time;
}

function candlesToSeries(candles: CandlePoint[]): CandlestickData<Time>[] {
  return candles.map((c) => ({
    time: toChartTime(c.time),
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  }));
}

export function CandlestickChart({ height = 350 }: { height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const candles = useTradingStore((s) => s.candles);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      width: containerRef.current.clientWidth,
      height,
      timeScale: { borderColor: "rgba(255,255,255,0.08)" },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const onResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || candles.length === 0) return;
    seriesRef.current.setData(candlesToSeries(candles));
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
