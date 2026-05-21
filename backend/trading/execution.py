import time
import MetaTrader5 as mt5
from typing import Dict, Any
from .mt5_broker import MT5Broker

class ExecutionService:
    def __init__(self, broker: MT5Broker):
        self.broker = broker
        self.max_retries = 3

    def execute_market_order(self, symbol: str, action: str, volume: float, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        if not self.broker.connected:
            if not self.broker.connect():
                return {"status": "error", "message": "Broker not connected"}

        order_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        
        # Get latest tick for current price
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

        # Retry logic for failed orders
        for attempt in range(self.max_retries):
            result = self.broker.send_order(request)
            if result and result.get("status") == "success":
                return result
                
            print(f"Order attempt {attempt + 1} failed. Retrying...")
            time.sleep(1) # wait before retry
            
        return {"status": "error", "message": "Max retries exceeded."}
