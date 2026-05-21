import MetaTrader5 as mt5
from typing import Dict, Any, Optional, List
from core.config import settings

class MT5Broker:
    def __init__(self):
        self.connected = False
        self.current_account_type = "DEMO"
        self._set_credentials("DEMO")

    def _set_credentials(self, account_type: str):
        if account_type == "LIVE":
            self.login = settings.MT5_LIVE_LOGIN
            self.password = settings.MT5_LIVE_PASSWORD
            self.server = settings.MT5_LIVE_SERVER
            self.current_account_type = "LIVE"
        else:
            self.login = settings.MT5_DEMO_LOGIN
            self.password = settings.MT5_DEMO_PASSWORD
            self.server = settings.MT5_DEMO_SERVER
            self.current_account_type = "DEMO"

    def switch_account(self, account_type: str) -> bool:
        """Switch between DEMO and LIVE accounts dynamically."""
        if account_type not in ["DEMO", "LIVE"]:
            return False
            
        self.disconnect()
        self._set_credentials(account_type)
        return self.connect()

    def connect(self) -> bool:
        if not mt5.initialize():
            print("MT5 initialize() failed, error code =", mt5.last_error())
            self.connected = False
            return False
            
        if self.login and self.password and self.server:
            authorized = mt5.login(self.login, password=self.password, server=self.server)
            if not authorized:
                print(f"Failed to connect to {self.current_account_type} MT5 account, error code =", mt5.last_error())
                self.connected = False
                return False
                
        self.connected = True
        print(f"Successfully connected to MT5 {self.current_account_type} account: {self.login}")
        return True

    def check_connection(self) -> bool:
        """Connection monitor - attempts reconnect if failed"""
        if not self.connected or mt5.terminal_info() is None:
            print("MT5 connection lost. Attempting reconnect...")
            return self.connect()
        return True

    def disconnect(self):
        mt5.shutdown()
        self.connected = False

    def get_symbol_info(self, symbol: str):
        self.check_connection()
        return mt5.symbol_info(symbol)
        
    def sync_active_trades(self) -> List[Dict[str, Any]]:
        """Real-time trade synchronization - pulls active positions from MT5"""
        if not self.check_connection():
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
                "time": pos.time
            }
            for pos in positions
        ]

    def send_order(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.check_connection():
            return {"status": "error", "message": "Not connected to MT5"}
        
        result = mt5.order_send(request)
        if result is None:
            return {"status": "error", "message": f"order_send failed: {mt5.last_error()}"}
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed, retcode={result.retcode}, comment={result.comment}")
            return {"status": "error", "retcode": result.retcode, "comment": result.comment}
            
        return {
            "status": "success",
            "order_ticket": result.order,
            "volume": result.volume,
            "price": result.price
        }
