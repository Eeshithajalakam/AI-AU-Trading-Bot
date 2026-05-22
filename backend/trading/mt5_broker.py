import logging
import time
from datetime import datetime, timedelta
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


class MT5Broker:
    def __init__(self) -> None:
        self.connected = False
        self.current_account_type = "DEMO"
        self._last_trade_time: datetime | None = None
        self.login = settings.mt5_login
        self.password = settings.mt5_password
        self.server = settings.mt5_server

    def switch_account(self, account_type: str) -> bool:
        if account_type == "LIVE":
            self.login = settings.MT5_LIVE_LOGIN or settings.mt5_login
            self.password = settings.MT5_LIVE_PASSWORD or settings.mt5_password
            self.server = settings.MT5_LIVE_SERVER or settings.mt5_server
            self.current_account_type = "LIVE"
        else:
            self.login = settings.MT5_DEMO_LOGIN or settings.mt5_login
            self.password = settings.MT5_DEMO_PASSWORD or settings.mt5_password
            self.server = settings.MT5_DEMO_SERVER or settings.mt5_server
            self.current_account_type = "DEMO"
        self.disconnect()
        return self.connect()

    def connect(self) -> bool:
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 not available on this platform")
            self.connected = settings.PAPER_TRADING_MODE
            return self.connected

        if not mt5.initialize():
            logger.error("MT5 initialize failed: %s", mt5.last_error())
            self.connected = False
            return False

        if self.login and self.password and self.server:
            if not mt5.login(self.login, password=self.password, server=self.server):
                logger.error("MT5 login failed: %s", mt5.last_error())
                self.connected = False
                return False

        self.connected = True
        logger.info("MT5 connected (%s) login=%s", self.current_account_type, self.login)
        return True

    def check_connection(self) -> bool:
        if settings.PAPER_TRADING_MODE and not MT5_AVAILABLE:
            return True
        if not MT5_AVAILABLE:
            return False
        if not self.connected or mt5.terminal_info() is None:
            return self.connect()
        return True

    def disconnect(self) -> None:
        if MT5_AVAILABLE:
            mt5.shutdown()
        self.connected = False

    @property
    def account_mode(self) -> str:
        return self.current_account_type

    def get_account_info(self) -> dict[str, Any]:
        if not MT5_AVAILABLE or not self.check_connection():
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "profit": 0.0,
                "currency": "USD",
                "paper": settings.PAPER_TRADING_MODE,
            }
        info = mt5.account_info()
        if info is None:
            return {}
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "profit": info.profit,
            "currency": info.currency,
            "login": info.login,
            "server": info.server,
            "paper": False,
        }

    def get_spread_points(self, symbol: str) -> float:
        if not MT5_AVAILABLE or not self.check_connection():
            return 0.0
        info = mt5.symbol_info(symbol)
        if info is None:
            return 999.0
        return float(info.spread)

    def is_spread_acceptable(self, symbol: str) -> bool:
        spread = self.get_spread_points(symbol)
        return spread <= settings.MAX_SPREAD_POINTS

    def is_cooldown_active(self) -> bool:
        if self._last_trade_time is None:
            return False
        elapsed = (datetime.utcnow() - self._last_trade_time).total_seconds()
        return elapsed < settings.TRADE_COOLDOWN_SECONDS

    def mark_trade_executed(self) -> None:
        self._last_trade_time = datetime.utcnow()

    def get_positions(self) -> list[dict[str, Any]]:
        return self.sync_active_trades()

    def sync_active_trades(self) -> list[dict[str, Any]]:
        if not MT5_AVAILABLE or not self.check_connection():
            return []
        positions = mt5.positions_get()
        if positions is None:
            return []
        return [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "time": pos.time,
            }
            for pos in positions
        ]

    def open_position_count(self, symbol: str | None = None) -> int:
        positions = self.sync_active_trades()
        if symbol:
            return len([p for p in positions if p["symbol"] == symbol])
        return len(positions)

    def close_position(self, ticket: int) -> dict[str, Any]:
        if not MT5_AVAILABLE or not self.check_connection():
            return {"status": "error", "message": "MT5 not available"}
        pos_list = mt5.positions_get(ticket=ticket)
        if not pos_list:
            return {"status": "error", "message": f"Position {ticket} not found"}
        pos = pos_list[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        if not tick:
            return {"status": "error", "message": "No tick data"}
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Bot Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        return self.send_order(request) or {"status": "error", "message": "Close failed"}

    def send_order(self, request: dict[str, Any]) -> dict[str, Any] | None:
        if not MT5_AVAILABLE:
            return None
        if not self.check_connection():
            return {"status": "error", "message": "Not connected to MT5"}
        result = mt5.order_send(request)
        if result is None:
            return {"status": "error", "message": f"order_send failed: {mt5.last_error()}"}
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {"status": "error", "retcode": result.retcode, "comment": result.comment}
        self.mark_trade_executed()
        return {
            "status": "success",
            "order_ticket": result.order,
            "volume": result.volume,
            "price": result.price,
        }
