import json
import os
from datetime import datetime
from typing import Dict, Any
from .mt5_broker import MT5Broker
from .validation import RiskValidator
from .risk_engine import RiskEngine
from .execution import ExecutionService
from core.notifications import notifier

class OrderManager:
    def __init__(self, account_balance: float = 10000.0):
        self.broker = MT5Broker()
        self.validator = RiskValidator()
        self.risk_engine = RiskEngine()
        self.executor = ExecutionService(self.broker)
        self.account_balance = account_balance
        self.trade_log_file = "trade_logs.json"

    def _log_trade(self, log_data: Dict[str, Any]):
        log_data["timestamp"] = datetime.utcnow().isoformat()
        try:
            logs = []
            if os.path.exists(self.trade_log_file):
                with open(self.trade_log_file, "r") as f:
                    logs = json.load(f)
            logs.append(log_data)
            with open(self.trade_log_file, "w") as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            print(f"Failed to log trade: {e}")

    def process_signal(self, signal: Dict[str, Any], volume: float = 0.01) -> Dict[str, Any]:
        """
        Process an AI signal and execute it if it passes validation.
        """
        signal_id = signal.get("id", f"sig-{datetime.utcnow().timestamp()}")
        asset = signal.get("asset", "XAU/USD")
        
        # MT5 uses XAUUSD instead of XAU/USD typically
        mt5_symbol = asset.replace("/", "")
        
        action = signal.get("action", "HOLD")
        if action == "HOLD":
            return {"status": "ignored", "message": "Signal is HOLD"}

        entry = signal.get("entry", 0.0)
        confidence = signal.get("confidence", 50.0)
        # Assuming ATR is passed in the signal metrics, default to 3.0 if missing
        atr = signal.get("metrics", {}).get("atr", 3.0)

        # 1. Global Risk Kill Switch
        risk_status = self.risk_engine.evaluate_emergency_status(self.account_balance)
        if not risk_status["safe"]:
            self._log_trade({"signal_id": signal_id, "status": "BLOCKED_EMERGENCY", "reason": risk_status["reason"]})
            return {"status": "rejected", "message": risk_status["reason"]}

        # 2. Duplicate check
        if not self.validator.validate_duplicate(signal_id):
            return {"status": "rejected", "message": "Duplicate signal"}

        # 3. Dynamic Volatility Risk Sizing & SL/TP
        risk_params = self.risk_engine.calculate_dynamic_risk(
            account_balance=self.account_balance,
            current_price=entry,
            action=action,
            atr=atr,
            ai_confidence=confidence
        )
        
        dynamic_volume = risk_params["volume"]
        dynamic_sl = risk_params["sl"]
        dynamic_tp = risk_params["tp"]

        # 4. Execution
        print(f"Executing {action} on {mt5_symbol} | Vol: {dynamic_volume} | SL: {dynamic_sl} | TP: {dynamic_tp}")
        result = self.executor.execute_market_order(
            symbol=mt5_symbol,
            action=action,
            volume=dynamic_volume,
            sl=dynamic_sl,
            tp=dynamic_tp
        )

        if result.get("status") == "success":
            self.validator.register_trade(signal_id, result)
            self.risk_engine.log_trade_result(0.0) # Assume 0 initial PnL on execution
            self._log_trade({
                "signal_id": signal_id,
                "status": "EXECUTED",
                "risk_profile": risk_params,
                "details": result
            })
            notifier.send_alert(
                title=f"Trade Executed: {action} {mt5_symbol}",
                message=f"Volume: {dynamic_volume}\nEntry Price: {result.get('price')}\nSL: {dynamic_sl} | TP: {dynamic_tp}",
                level="SUCCESS"
            )
        else:
            self._log_trade({
                "signal_id": signal_id,
                "status": "FAILED",
                "error": result.get("message", "Unknown error")
            })

        return result
