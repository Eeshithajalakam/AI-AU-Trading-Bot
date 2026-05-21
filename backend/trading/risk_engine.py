from typing import Dict, Any
from ai.news_intelligence import news_engine
from core.notifications import notifier

class RiskEngine:
    def __init__(self):
        self.emergency_shutdown = False
        self.max_daily_drawdown_pct = 0.05  # 5% daily loss limit
        self.max_trade_risk_pct = 0.02      # 2% max risk per trade
        self.current_daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 15

    def evaluate_emergency_status(self, account_balance: float) -> Dict[str, Any]:
        """Check for catastrophic scenarios to trigger global kill switch."""
        if self.emergency_shutdown:
            return {"safe": False, "reason": "EMERGENCY_SHUTDOWN_ACTIVE"}
            
        if self.current_daily_pnl < -(account_balance * self.max_daily_drawdown_pct):
            if not self.emergency_shutdown:
                notifier.send_alert("EMERGENCY SHUTDOWN", f"Daily drawdown limit ({self.max_daily_drawdown_pct*100}%) exceeded. Trading halted.", "CRITICAL")
            self.emergency_shutdown = True
            return {"safe": False, "reason": "DAILY_DRAWDOWN_LIMIT_EXCEEDED"}
            
        if self.daily_trades >= self.max_daily_trades:
            return {"safe": False, "reason": "MAX_DAILY_TRADES_REACHED"}
            
        # 4. Macroeconomic News Intelligence Halt
        news_env = news_engine.analyze_current_environment()
        if news_env["danger_zone"]:
            events = ", ".join(news_env["active_high_impact_events"])
            
            # Fire alert if we just entered the danger zone (using a simple log for now so we don't spam)
            return {"safe": False, "reason": f"TRADE_PAUSE_MACRO_EVENT: {events}"}
            
        return {"safe": True, "reason": "OK"}

    def calculate_dynamic_risk(
        self, 
        account_balance: float, 
        current_price: float, 
        action: str, 
        atr: float, 
        ai_confidence: float
    ) -> Dict[str, float]:
        """
        Calculates volatility-adjusted position size and dynamic SL/TP.
        - AI Confidence tightens SL and extends TP.
        - High ATR (Volatility) reduces lot size.
        """
        # 1. Dynamic SL & TP Calculation
        sl_multiplier = 1.5
        tp_multiplier = 3.0
        
        # AI Risk Scoring adjustment
        if ai_confidence > 75:
            sl_multiplier = 1.2 # Tighter SL on high conviction
            tp_multiplier = 4.0 # Extended TP
        elif ai_confidence < 50:
            sl_multiplier = 2.0 # Wider SL to avoid chop
            tp_multiplier = 2.0 # Conservative TP
            
        sl_distance = atr * sl_multiplier if atr > 0 else 5.0
        tp_distance = atr * tp_multiplier if atr > 0 else 10.0
        
        if action == "BUY":
            sl = current_price - sl_distance
            tp = current_price + tp_distance
        else:
            sl = current_price + sl_distance
            tp = current_price - tp_distance

        # 2. Volatility-Adjusted Position Sizing
        base_risk_amount = account_balance * self.max_trade_risk_pct
        
        # Volatility penalty mapping (assume XAU ATR usually 3-5)
        volatility_penalty = 1.0
        if atr > 8.0:
            volatility_penalty = 0.5 # Halve the risk in extreme chop
        elif atr < 2.0:
            volatility_penalty = 1.2 # Slight risk increase in calm conditions
            
        adjusted_risk_amount = base_risk_amount * volatility_penalty
        
        # XAU contract size is typically 100 oz
        if sl_distance > 0:
            lot_size = adjusted_risk_amount / (sl_distance * 100)
        else:
            lot_size = 0.01
            
        # Clamp bounds
        lot_size = max(0.01, min(round(lot_size, 2), 5.0))
        
        return {
            "volume": lot_size,
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "risk_amount": round(adjusted_risk_amount, 2)
        }
        
    def log_trade_result(self, pnl: float):
        """Update daily PnL and trade count for drawdown monitoring"""
        self.current_daily_pnl += pnl
        self.daily_trades += 1
