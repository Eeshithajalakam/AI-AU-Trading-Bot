import logging
import random
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from core.deps import ai_service
from services.market_engine import market_engine

logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.risk_per_trade = 0.02
        self.ai_service = ai_service

    async def load_historical_data(self, days: int = 30) -> pd.DataFrame:
        period = "60d" if days > 30 else "30d"
        try:
            df = await market_engine.fetch_historical(period=period)
            df = df.set_index("timestamp")
            bars_needed = days * 24 * 4
            return df.tail(min(bars_needed, len(df)))
        except Exception as e:
            logger.warning("Using synthetic data for backtest: %s", e)
            return self.generate_dummy_data(days)

    def generate_dummy_data(self, days: int = 30) -> pd.DataFrame:
        now = datetime.utcnow()
        timestamps = [now - timedelta(minutes=i * 15) for i in range(days * 24 * 4, 0, -1)]
        prices = [2350.0]
        for _ in range(1, len(timestamps)):
            prices.append(prices[-1] + np.random.normal(0, 1.2))
        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": [p - abs(np.random.normal(0, 0.5)) for p in prices],
            "high": [p + abs(np.random.normal(0, 1.0)) for p in prices],
            "low": [p - abs(np.random.normal(0, 1.0)) for p in prices],
            "close": prices,
            "volume": [abs(np.random.normal(100, 20)) for _ in prices],
        })
        return df.set_index("timestamp")

    async def run_backtest(self, df: pd.DataFrame) -> dict[str, Any]:
        capital = self.initial_capital
        peak_capital = capital
        trades = []
        pnl_history = [capital]

        for i in range(100, len(df), 4):
            window = df.iloc[i - 100 : i]
            try:
                signal = await self.ai_service.analyze_market_data(window)
            except Exception:
                continue

            action = signal["action"]
            if action not in ("BUY", "SELL"):
                continue

            current_price = float(window["close"].iloc[-1])
            confidence = signal["confidence_score"]
            atr = signal.get("metrics", {}).get("atr", 3.0)
            sl_dist = atr * 1.5
            tp_dist = atr * 3.0

            risk_amount = capital * self.risk_per_trade
            lot_size = risk_amount / max(sl_dist * 100, 1)

            next_idx = min(i + 4, len(df) - 1)
            exit_price = float(df["close"].iloc[next_idx])
            if action == "BUY":
                profit = (exit_price - current_price) * lot_size * 100
            else:
                profit = (current_price - exit_price) * lot_size * 100

            confidence_factor = 0.5 + (confidence / 100) * 0.5
            profit *= confidence_factor

            capital += profit
            peak_capital = max(peak_capital, capital)
            pnl_history.append(capital)
            trades.append({
                "timestamp": window.index[-1].isoformat(),
                "action": action,
                "confidence": confidence,
                "price": current_price,
                "exit_price": exit_price,
                "profit": round(profit, 2),
                "capital": round(capital, 2),
            })

        return self._generate_report(trades, pnl_history)

    def _generate_report(self, trades: list[dict], pnl_history: list[float]) -> dict[str, Any]:
        if not trades:
            return {"error": "No trades executed during this period."}

        wins = [t for t in trades if t["profit"] > 0]
        losses = [t for t in trades if t["profit"] <= 0]
        win_rate = len(wins) / len(trades) if trades else 0.0
        gross_profit = sum(t["profit"] for t in wins)
        gross_loss = abs(sum(t["profit"] for t in losses))
        net_profit = gross_profit - gross_loss
        roi = (net_profit / self.initial_capital) * 100

        returns = pd.Series(pnl_history).pct_change().dropna()
        sharpe = (
            (returns.mean() / returns.std()) * np.sqrt(252)
            if len(returns) > 1 and returns.std() != 0
            else 0.0
        )

        peak = pd.Series(pnl_history).expanding(min_periods=1).max()
        dd = (pd.Series(pnl_history) - peak) / peak
        max_dd = abs(dd.min()) * 100

        return {
            "summary": {
                "initial_capital": self.initial_capital,
                "final_capital": round(pnl_history[-1], 2),
                "net_profit": round(net_profit, 2),
                "roi_pct": round(roi, 2),
                "total_trades": len(trades),
                "win_rate_pct": round(win_rate * 100, 2),
                "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0,
            },
            "metrics": {
                "sharpe_ratio": round(sharpe, 2),
                "max_drawdown_pct": round(max_dd, 2),
                "average_win_usd": round(gross_profit / len(wins), 2) if wins else 0.0,
                "average_loss_usd": round(gross_loss / len(losses), 2) if losses else 0.0,
            },
            "equity_curve": pnl_history[:: max(1, len(pnl_history) // 100)],
            "recent_trades": trades[-20:],
        }
