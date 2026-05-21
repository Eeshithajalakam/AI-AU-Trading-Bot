import time
from typing import Dict, Any

class RiskValidator:
    def __init__(self):
        self.max_risk_pct = 0.02  # 2% max risk per trade
        self.max_daily_trades = 10
        self.daily_trades = 0
        self.active_trades: Dict[str, Dict[str, Any]] = {}

    def validate_duplicate(self, signal_id: str) -> bool:
        # Prevent duplicate execution of the same signal
        if signal_id in self.active_trades:
            return False
        return True

    def validate_risk(self, account_balance: float, entry: float, sl: float, volume: float) -> bool:
        if self.daily_trades >= self.max_daily_trades:
            print("Risk: Max daily trades reached.")
            return False
            
        # Simplistic risk calculation based on entry and stop loss
        if sl <= 0:
            print("Risk: Invalid Stop Loss (0 or negative).")
            return False
            
        risk_per_unit = abs(entry - sl)
        total_risk = risk_per_unit * volume * 100 # assuming standard lot scaling (e.g. 100 oz per lot for XAU)
        
        # In a real environment, contract size and exact tick value should be queried from MT5.
        if total_risk > (account_balance * self.max_risk_pct):
            print(f"Risk too high: {total_risk} > {account_balance * self.max_risk_pct}")
            return False
            
        return True
        
    def register_trade(self, signal_id: str, trade_data: Dict[str, Any]):
        self.active_trades[signal_id] = trade_data
        self.daily_trades += 1
