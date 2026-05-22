import json
import logging
import os
from datetime import datetime
from typing import Any

from core.config import settings
from core.database import AsyncSessionLocal
from db.repository import TradeRepository
from .mt5_broker import MT5Broker
from .validation import RiskValidator
from .risk_engine import RiskEngine
from .execution import ExecutionService
from core.notifications import notifier

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, account_balance: float = 10000.0) -> None:
        self.broker = MT5Broker()
        self.validator = RiskValidator()
        self.risk_engine = RiskEngine()
        self.executor = ExecutionService(self.broker)
        self.account_balance = account_balance
        self.trade_log_file = "trade_logs.json"
        self._sync_account_balance()

    def _sync_account_balance(self) -> None:
        info = self.broker.get_account_info()
        if info.get("balance"):
            self.account_balance = float(info["balance"])

    async def _persist_trade(self, data: dict[str, Any]) -> None:
        try:
            async with AsyncSessionLocal() as session:
                await TradeRepository.create(session, data)
        except Exception as e:
            logger.warning("DB trade persist failed: %s", e)

    def _log_trade(self, log_data: dict[str, Any]) -> None:
        log_data["timestamp"] = datetime.utcnow().isoformat()
        try:
            logs = []
            if os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, "r") as f:
                    logs = json.load(f)
            logs.append(log_data)
            with open(self.trade_log_file, "w") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.warning("JSON trade log failed: %s", e)

    def process_signal(self, signal: dict[str, Any], volume: float = 0.01) -> dict[str, Any]:
        if not settings.AUTO_TRADE_ENABLED:
            return {"status": "ignored", "message": "AUTO_TRADE_ENABLED is false"}

        signal_id = signal.get("id", f"sig-{datetime.utcnow().timestamp()}")
        asset = signal.get("asset", "XAU/USD")
        mt5_symbol = settings.MT5_SYMBOL if asset.replace("/", "") == "XAUUSD" else asset.replace("/", "")

        action = signal.get("action", "HOLD")
        if action == "HOLD":
            sig_type = signal.get("type", "")
            if sig_type == "LONG":
                action = "BUY"
            elif sig_type == "SHORT":
                action = "SELL"
        if action == "HOLD":
            return {"status": "ignored", "message": "Signal is HOLD"}

        entry = float(signal.get("entry", 0.0))
        confidence = float(signal.get("confidence", signal.get("confidence_score", 50.0)))
        atr = float(signal.get("metrics", {}).get("atr", 3.0))

        self._sync_account_balance()

        # Safeguards
        if self.broker.is_cooldown_active():
            return {"status": "rejected", "message": "Trade cooldown active"}

        open_count = self.broker.open_position_count(mt5_symbol)
        if settings.PAPER_TRADING_MODE:
            open_count = len(self.executor.get_paper_positions())
        if open_count >= settings.MAX_OPEN_TRADES:
            return {"status": "rejected", "message": f"Max open trades ({settings.MAX_OPEN_TRADES}) reached"}

        spread = self.broker.get_spread_points(mt5_symbol) if hasattr(self.broker, "get_spread_points") else 0
        risk_status = self.risk_engine.evaluate_emergency_status(self.account_balance, spread_points=spread)
        if not risk_status["safe"]:
            self._log_trade({"signal_id": signal_id, "status": "BLOCKED", "reason": risk_status["reason"]})
            return {"status": "rejected", "message": risk_status["reason"]}

        if self.risk_engine.current_daily_pnl < -settings.MAX_DAILY_LOSS_USD:
            return {"status": "rejected", "message": "Max daily loss USD limit reached"}

        if not self.validator.validate_duplicate(signal_id):
            return {"status": "rejected", "message": "Duplicate signal"}

        regime = signal.get("regime", {}).get("regime", "ranging") if isinstance(signal.get("regime"), dict) else "ranging"
        risk_params = self.risk_engine.calculate_dynamic_risk(
            account_balance=self.account_balance,
            current_price=entry,
            action=action,
            atr=atr,
            ai_confidence=confidence,
            regime=regime,
        )
        dynamic_volume = risk_params["volume"]
        dynamic_sl = risk_params["sl"]
        dynamic_tp = risk_params["tp"]

        logger.info(
            "Executing %s %s vol=%.2f sl=%.2f tp=%.2f paper=%s",
            action, mt5_symbol, dynamic_volume, dynamic_sl, dynamic_tp, settings.PAPER_TRADING_MODE,
        )

        result = self.executor.execute_market_order(
            symbol=mt5_symbol,
            action=action,
            volume=dynamic_volume,
            sl=dynamic_sl,
            tp=dynamic_tp,
            entry_hint=entry,
        )

        trade_record = {
            "signal_id": signal_id,
            "symbol": mt5_symbol,
            "action": action,
            "volume": dynamic_volume,
            "entry_price": result.get("price", entry),
            "sl": dynamic_sl,
            "tp": dynamic_tp,
            "status": "EXECUTED" if result.get("status") == "success" else "FAILED",
            "paper_trade": settings.PAPER_TRADING_MODE or result.get("paper", False),
            "mt5_ticket": result.get("order_ticket"),
            "details": {"risk_profile": risk_params, "execution": result},
        }

        self._log_trade(trade_record)

        if result.get("status") == "success":
            self.validator.register_trade(signal_id, result)
            self.risk_engine.log_trade_result(0.0)
            notifier.send_alert(
                title=f"Trade {'[PAPER] ' if trade_record['paper_trade'] else ''}{action} {mt5_symbol}",
                message=f"Vol: {dynamic_volume} @ {result.get('price')} | SL: {dynamic_sl} TP: {dynamic_tp}",
                level="SUCCESS",
            )
        else:
            trade_record["status"] = "FAILED"

        return {**result, "trade_record": trade_record}

    def get_live_status(self) -> dict[str, Any]:
        self._sync_account_balance()
        positions = self.executor.get_paper_positions() if settings.PAPER_TRADING_MODE else self.broker.get_positions()
        return {
            "account": self.broker.get_account_info(),
            "positions": positions,
            "position_count": len(positions),
            "paper_mode": settings.PAPER_TRADING_MODE,
            "auto_trade": settings.AUTO_TRADE_ENABLED,
            "cooldown_active": self.broker.is_cooldown_active(),
            "daily_pnl": self.risk_engine.current_daily_pnl,
        }
