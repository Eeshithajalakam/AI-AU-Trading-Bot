"""Institutional-grade risk engine for live-trading readiness."""

from datetime import datetime, timezone
from typing import Any

from ai.news_intelligence import news_engine
from core.config import settings
from core.notifications import notifier


class RiskEngine:
    def __init__(self) -> None:
        self.emergency_shutdown = False
        self.capital_preservation_mode = settings.CAPITAL_PRESERVATION_MODE
        self.max_daily_drawdown_pct = settings.MAX_DRAWDOWN_PCT
        self.max_trade_risk_pct = 0.015
        self.current_daily_pnl = 0.0
        self.peak_equity = 0.0
        self.current_equity = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 12
        self.consecutive_losses = 0
        self.last_trade_won: bool | None = None

    def sync_equity(self, balance: float, equity: float) -> None:
        self.current_equity = equity
        if self.peak_equity <= 0:
            self.peak_equity = equity
        self.peak_equity = max(self.peak_equity, equity)
        dd = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
        if dd >= self.max_daily_drawdown_pct and not self.emergency_shutdown:
            self.emergency_shutdown = True
            notifier.send_alert(
                "DRAWDOWN KILL SWITCH",
                f"Equity drawdown {dd*100:.2f}% exceeded limit",
                "CRITICAL",
            )

    def _in_trading_hours(self) -> bool:
        hour = datetime.now(timezone.utc).hour
        return settings.TRADING_HOURS_UTC_START <= hour < settings.TRADING_HOURS_UTC_END

    def evaluate_emergency_status(
        self,
        account_balance: float,
        spread_points: float = 0.0,
    ) -> dict[str, Any]:
        if self.emergency_shutdown:
            return {"safe": False, "reason": "EMERGENCY_SHUTDOWN_ACTIVE", "code": "KILL"}

        if self.capital_preservation_mode or settings.CAPITAL_PRESERVATION_MODE:
            return {"safe": False, "reason": "CAPITAL_PRESERVATION_MODE", "code": "PRESERVE"}

        if not self._in_trading_hours():
            return {"safe": False, "reason": "OUTSIDE_TRADING_HOURS", "code": "HOURS"}

        if self.current_daily_pnl < -settings.MAX_DAILY_LOSS_USD:
            self.emergency_shutdown = True
            notifier.send_alert("DAILY LOSS LIMIT", f"Lost ${abs(self.current_daily_pnl):.2f} today", "CRITICAL")
            return {"safe": False, "reason": "MAX_DAILY_LOSS_USD", "code": "DAILY_LOSS"}

        if self.current_daily_pnl < -(account_balance * self.max_daily_drawdown_pct):
            self.emergency_shutdown = True
            return {"safe": False, "reason": "DAILY_DRAWDOWN_LIMIT", "code": "DRAWDOWN"}

        if self.consecutive_losses >= settings.MAX_CONSECUTIVE_LOSSES:
            return {"safe": False, "reason": f"CONSECUTIVE_LOSSES_{self.consecutive_losses}", "code": "STREAK"}

        if self.daily_trades >= self.max_daily_trades:
            return {"safe": False, "reason": "MAX_DAILY_TRADES", "code": "TRADE_CAP"}

        if spread_points > settings.MAX_SPREAD_POINTS:
            return {"safe": False, "reason": f"SPREAD_TOO_WIDE_{spread_points:.1f}", "code": "SPREAD"}

        news_env = news_engine.analyze_current_environment()
        if news_env["danger_zone"]:
            events = ", ".join(news_env["active_high_impact_events"])
            return {"safe": False, "reason": f"MACRO_HALT: {events}", "code": "NEWS"}

        return {"safe": True, "reason": "OK", "code": "PASS"}

    def kelly_volume(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        account_balance: float,
        sl_distance: float,
    ) -> float:
        if avg_loss <= 0 or sl_distance <= 0:
            return 0.01
        b = avg_win / avg_loss
        p = max(0.01, min(win_rate, 0.99))
        q = 1 - p
        kelly = (p * b - q) / b if b > 0 else 0
        kelly = max(0, kelly) * settings.KELLY_FRACTION
        risk_amount = account_balance * kelly
        lots = risk_amount / (sl_distance * 100)
        return max(0.01, min(round(lots, 2), 3.0))

    def calculate_dynamic_risk(
        self,
        account_balance: float,
        current_price: float,
        action: str,
        atr: float,
        ai_confidence: float,
        regime: str = "ranging",
        win_rate: float = 0.55,
    ) -> dict[str, float]:
        sl_mult = 1.5
        tp_mult = 3.0

        if ai_confidence > 78:
            sl_mult, tp_mult = 1.1, 4.0
        elif ai_confidence < 52:
            sl_mult, tp_mult = 2.2, 2.0

        if regime == "high_volatility":
            sl_mult *= 1.3
            tp_mult *= 1.2
        elif regime == "ranging":
            tp_mult *= 0.85

        sl_distance = max(atr * sl_mult, 2.0)
        tp_distance = max(atr * tp_mult, sl_distance * settings.MIN_RISK_REWARD)

        if action == "BUY":
            sl = current_price - sl_distance
            tp = current_price + tp_distance
        else:
            sl = current_price + sl_distance
            tp = current_price - tp_distance

        rr = tp_distance / sl_distance if sl_distance > 0 else 0
        if rr < settings.MIN_RISK_REWARD:
            tp_distance = sl_distance * settings.MIN_RISK_REWARD
            tp = current_price + tp_distance if action == "BUY" else current_price - tp_distance

        if settings.USE_KELLY_SIZING:
            lot_size = self.kelly_volume(win_rate, tp_distance, sl_distance, account_balance, sl_distance)
        else:
            risk_amount = account_balance * self.max_trade_risk_pct
            if regime == "high_volatility":
                risk_amount *= 0.5
            lot_size = risk_amount / (sl_distance * 100) if sl_distance > 0 else 0.01

        confidence_scale = 0.5 + (ai_confidence / 100) * 0.5
        lot_size = max(0.01, min(round(lot_size * confidence_scale, 2), 2.0))

        risk_score = round(min(100, (ai_confidence * 0.4) + (rr * 15) + (20 if regime == "trending" else 0)), 1)

        return {
            "volume": lot_size,
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "risk_amount": round(account_balance * self.max_trade_risk_pct * confidence_scale, 2),
            "risk_reward": round(rr, 2),
            "risk_score": risk_score,
            "sl_distance": round(sl_distance, 2),
            "tp_distance": round(tp_distance, 2),
        }

    def log_trade_result(self, pnl: float) -> None:
        self.current_daily_pnl += pnl
        self.daily_trades += 1
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_trade_won = False
        else:
            self.consecutive_losses = 0
            self.last_trade_won = True

    def status_dict(self) -> dict[str, Any]:
        return {
            "emergency_shutdown": self.emergency_shutdown,
            "capital_preservation": self.capital_preservation_mode,
            "daily_pnl": round(self.current_daily_pnl, 2),
            "daily_trades": self.daily_trades,
            "consecutive_losses": self.consecutive_losses,
            "peak_equity": self.peak_equity,
        }
