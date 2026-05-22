"""Real-time and historical XAU/USD OHLCV via Yahoo Finance (GC=F gold futures)."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from core.config import settings

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self) -> None:
        self.symbol = settings.MARKET_SYMBOL
        self.interval = settings.MARKET_INTERVAL
        self._history: list[dict[str, Any]] = []
        self._current_price: float = 2350.0
        self._last_fetch: datetime | None = None

    @property
    def current_price(self) -> float:
        return self._current_price

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history

    def _fetch_yfinance_sync(self, period: str = "5d", interval: str | None = None) -> pd.DataFrame:
        import yfinance as yf

        interval = interval or self.interval
        ticker = yf.Ticker(self.symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data returned for {self.symbol}")
        df = df.reset_index()
        col_map = {c: c.lower() for c in df.columns}
        df = df.rename(columns=col_map)
        ts_col = "datetime" if "datetime" in df.columns else "date"
        df = df.rename(columns={ts_col: "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna()

    async def fetch_historical(self, period: str = "5d") -> pd.DataFrame:
        return await asyncio.to_thread(self._fetch_yfinance_sync, period, self.interval)

    async def bootstrap_history(self, min_bars: int = 100) -> None:
        df = await self.fetch_historical(period="5d")
        records = []
        for _, row in df.tail(min_bars).iterrows():
            ts = row["timestamp"]
            if hasattr(ts, "to_pydatetime"):
                ts = ts.to_pydatetime()
            records.append({
                "timestamp": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
        self._history = records
        if records:
            self._current_price = records[-1]["close"]
        self._last_fetch = datetime.utcnow()
        logger.info("Bootstrapped %d bars for %s @ %.2f", len(records), self.symbol, self._current_price)

    async def refresh_latest(self) -> dict[str, Any] | None:
        try:
            df = await asyncio.to_thread(self._fetch_yfinance_sync, "1d", "1m")
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
            self._current_price = bar["close"]
            if self._history:
                last_ts = self._history[-1]["timestamp"]
                if bar["timestamp"] != last_ts:
                    self._history.append(bar)
                else:
                    self._history[-1] = bar
            else:
                self._history.append(bar)
            if len(self._history) > 500:
                self._history = self._history[-500:]
            return bar
        except Exception as e:
            logger.warning("Market refresh failed: %s", e)
            return None

    def append_synthetic_tick(self) -> dict[str, Any]:
        """Fallback tick when live feed is unavailable."""
        import random

        delta = (random.random() - 0.48) * 0.8
        self._current_price = round(self._current_price + delta, 2)
        now = datetime.utcnow()
        bar = {
            "timestamp": now,
            "open": self._current_price - 0.3,
            "high": self._current_price + 0.5,
            "low": self._current_price - 0.5,
            "close": self._current_price,
            "volume": 100.0,
        }
        self._history.append(bar)
        if len(self._history) > 500:
            self._history.pop(0)
        return bar

    def to_dataframe(self) -> pd.DataFrame:
        if not self._history:
            return pd.DataFrame()
        df = pd.DataFrame(self._history)
        return df.set_index("timestamp")

    def price_points_for_frontend(self, limit: int = 120) -> list[dict[str, Any]]:
        points = []
        for bar in self._history[-limit:]:
            ts = bar["timestamp"]
            iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            points.append({"time": iso, "price": round(bar["close"], 2)})
        return points

    def ohlcv_for_frontend(self, limit: int = 120) -> list[dict[str, Any]]:
        candles = []
        for bar in self._history[-limit:]:
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


market_data_service = MarketDataService()
