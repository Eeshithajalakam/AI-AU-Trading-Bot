import logging
import time
from typing import Any

from core.config import settings
from .mt5_broker import MT5Broker, MT5_AVAILABLE

logger = logging.getLogger(__name__)

if MT5_AVAILABLE:
    import MetaTrader5 as mt5


class ExecutionService:
    def __init__(self, broker: MT5Broker) -> None:
        self.broker = broker
        self.max_retries = 3
        self._paper_positions: list[dict[str, Any]] = []
        self._paper_ticket = 100000

    def execute_market_order(
        self,
        symbol: str,
        action: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        entry_hint: float | None = None,
    ) -> dict[str, Any]:
        if settings.PAPER_TRADING_MODE or not MT5_AVAILABLE:
            return self._execute_paper(symbol, action, volume, sl, tp, entry_hint)

        if not self.broker.connected and not self.broker.connect():
            return {"status": "error", "message": "Broker not connected"}

        if not self.broker.is_spread_acceptable(symbol):
            return {"status": "rejected", "message": f"Spread too wide (max {settings.MAX_SPREAD_POINTS})"}

        order_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {"status": "error", "message": f"Could not get tick for {symbol}"}

        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Bot Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        for attempt in range(self.max_retries):
            result = self.broker.send_order(request)
            if result and result.get("status") == "success":
                return result
            logger.warning("Order attempt %d failed", attempt + 1)
            time.sleep(1)

        return {"status": "error", "message": "Max retries exceeded"}

    def _execute_paper(
        self,
        symbol: str,
        action: str,
        volume: float,
        sl: float,
        tp: float,
        entry_hint: float | None,
    ) -> dict[str, Any]:
        self._paper_ticket += 1
        price = entry_hint or 2350.0
        pos = {
            "ticket": self._paper_ticket,
            "symbol": symbol,
            "volume": volume,
            "type": action.upper(),
            "open_price": price,
            "sl": sl,
            "tp": tp,
            "profit": 0.0,
            "paper": True,
        }
        self._paper_positions.append(pos)
        logger.info("Paper trade: %s %s %.2f lots @ %.2f", action, symbol, volume, price)
        return {"status": "success", "order_ticket": self._paper_ticket, "volume": volume, "price": price, "paper": True}

    def close_position(self, ticket: int) -> dict[str, Any]:
        if settings.PAPER_TRADING_MODE or not MT5_AVAILABLE:
            self._paper_positions = [p for p in self._paper_positions if p["ticket"] != ticket]
            return {"status": "success", "message": "Paper position closed", "ticket": ticket}
        return self.broker.close_position(ticket)

    def get_paper_positions(self) -> list[dict[str, Any]]:
        return list(self._paper_positions)
