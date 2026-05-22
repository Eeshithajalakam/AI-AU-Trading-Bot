"""Production market data engine: multi-timeframe, validation, monitoring."""

import logging
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from core.config import settings

logger = logging.getLogger(__name__)

TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
}


class MarketEngine:
    def __init__(self) -> None:
        self.symbol = settings.MARKET_SYMBOL
        self._bars: dict[str, list[dict[str, Any]]] = {tf: [] for tf in TIMEFRAMES}
        self._current_price: float = 2350.0
        self._last_fetch_ms: float = 0.0
        self._spread_points: float = 0.0
        self._session: str = "unknown"
        self._heartbeat_at: datetime = datetime.now(timezone.utc)

    @property
    def current_price(self) -> float:
        return self._current_price

    @property
    def latency_ms(self) -> float:
        return max(0.0, (time.time() * 1000) - self._last_fetch_ms) if self._last_fetch_ms else 0.0

    def _fetch_sync(self, period: str, interval: str) -> pd.DataFrame:
        import yfinance as yf

        df = yf.Ticker(self.symbol).history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data for {self.symbol}")
        df = df.reset_index()
        col_map = {c: c.lower() for c in df.columns}
        df = df.rename(columns=col_map)
        ts_col = "datetime" if "datetime" in df.columns else "date"
        df = df.rename(columns={ts_col: "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna()

    def _validate_candle(self, bar: dict[str, Any]) -> bool:
        o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
        if any(x <= 0 for x in (o, h, l, c)):
            return False
        if h < max(o, c) or l > min(o, c):
            return False
        if h < l:
            return False
        return True

    def _detect_session(self) -> str:
        hour = datetime.now(timezone.utc).hour
        if 13 <= hour < 21:
            return "london_ny_overlap"
        if 8 <= hour < 17:
            return "london"
        if 13 <= hour < 22:
            return "new_york"
        return "asia"

    async def fetch_historical(self, period: str = "60d", interval: str | None = None) -> pd.DataFrame:
        import asyncio
        return await asyncio.to_thread(self._fetch_sync, period, interval or settings.MARKET_INTERVAL)

    async def bootstrap(self) -> None:
        import asyncio

        for tf, interval in TIMEFRAMES.items():
            period = "5d" if tf in ("1m", "5m") else "60d"
            try:
                df = await asyncio.to_thread(self._fetch_sync, period, interval)
                records = []
                for _, row in df.tail(200).iterrows():
                    ts = row["timestamp"]
                    if hasattr(ts, "to_pydatetime"):
                        ts = ts.to_pydatetime()
                    bar = {
                        "timestamp": ts,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    }
                    if self._validate_candle(bar):
                        records.append(bar)
                self._bars[tf] = records
            except Exception as e:
                logger.warning("Bootstrap %s failed: %s", tf, e)

        if self._bars.get("1m"):
            self._current_price = self._bars["1m"][-1]["close"]
        self._session = self._detect_session()
        self._heartbeat_at = datetime.now(timezone.utc)
        logger.info("Market engine bootstrapped — price=%.2f session=%s", self._current_price, self._session)

    async def refresh(self) -> dict[str, Any] | None:
        import asyncio

        t0 = time.time()
        try:
            df = await asyncio.to_thread(self._fetch_sync, "1d", "1m")
            if df.empty:
                return None
            row = df.iloc[-1]
            ts = row["timestamp"]
            if hasattr(ts, "to_pydatetime"):
                ts = ts.to_pydatetime()
            bar = {
                "timestamp": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            if not self._validate_candle(bar):
                return None

            self._current_price = bar["close"]
            self._last_fetch_ms = t0 * 1000
            self._session = self._detect_session()
            self._heartbeat_at = datetime.now(timezone.utc)

            for tf in ("1m",):
                hist = self._bars[tf]
                if hist and bar["timestamp"] == hist[-1]["timestamp"]:
                    hist[-1] = bar
                else:
                    hist.append(bar)
                if len(hist) > 500:
                    self._bars[tf] = hist[-500:]

            return bar
        except Exception as e:
            logger.warning("Market refresh failed: %s", e)
            return None

    def append_synthetic_tick(self) -> dict[str, Any]:
        import random

        delta = (random.random() - 0.48) * 0.6
        self._current_price = round(self._current_price + delta, 2)
        now = datetime.now(timezone.utc)
        bar = {
            "timestamp": now,
            "open": self._current_price - 0.2,
            "high": self._current_price + 0.4,
            "low": self._current_price - 0.4,
            "close": self._current_price,
            "volume": 100.0,
        }
        self._bars["1m"].append(bar)
        if len(self._bars["1m"]) > 500:
            self._bars["1m"].pop(0)
        return bar

    def get_dataframe(self, timeframe: str = "1m") -> pd.DataFrame:
        bars = self._bars.get(timeframe, [])
        if not bars:
            return pd.DataFrame()
        return pd.DataFrame(bars).set_index("timestamp")

    def get_multi_timeframe_summary(self) -> dict[str, Any]:
        summary = {}
        for tf in TIMEFRAMES:
            df = self.get_dataframe(tf)
            if len(df) < 2:
                continue
            summary[tf] = {
                "close": float(df["close"].iloc[-1]),
                "change_pct": float(df["close"].pct_change().iloc[-1] * 100),
                "bars": len(df),
            }
        return summary

    def ohlcv_for_frontend(self, timeframe: str = "1m", limit: int = 120) -> list[dict]:
        candles = []
        for bar in self._bars.get(timeframe, [])[-limit:]:
            ts = bar["timestamp"]
            iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            candles.append({
                "time": iso,
                "open": round(bar["open"], 2),
                "high": round(bar["high"], 2),
                "low": round(bar["low"], 2),
                "close": round(bar["close"], 2),
                "volume": round(bar["volume"], 2),
            })
        return candles

    def price_points_for_frontend(self, limit: int = 120) -> list[dict]:
        return [
            {"time": c["time"], "price": c["close"]}
            for c in self.ohlcv_for_frontend("1m", limit)
        ]

    def health_snapshot(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self._current_price,
            "session": self._session,
            "latency_ms": round(self.latency_ms, 1),
            "spread_points": self._spread_points,
            "heartbeat": self._heartbeat_at.isoformat(),
            "timeframes": {tf: len(b) for tf, b in self._bars.items()},
        }


market_engine = MarketEngine()

# Backward compatibility alias
market_data_service = market_engine
