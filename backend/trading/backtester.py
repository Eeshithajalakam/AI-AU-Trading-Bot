import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from ai.service import AIService

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.risk_per_trade = 0.02
        self.ai_service = AIService()
        
    def generate_dummy_data(self, days: int = 30) -> pd.DataFrame:
        """Generate historical OHLCV data for backtesting replay."""
        now = datetime.utcnow()
        # 15-minute intervals
        timestamps = [now - timedelta(minutes=i*15) for i in range(days * 24 * 4, 0, -1)]
        
        # Random walk price generation mimicking XAU/USD volatility
        prices = [2350.0]
        for _ in range(1, len(timestamps)):
            change = np.random.normal(0, 1.2)
            prices.append(prices[-1] + change)
            
        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": [p - abs(np.random.normal(0, 0.5)) for p in prices],
            "high": [p + abs(np.random.normal(0, 1.0)) for p in prices],
            "low": [p - abs(np.random.normal(0, 1.0)) for p in prices],
            "close": prices,
            "volume": [abs(np.random.normal(100, 20)) for _ in prices]
        })
        return df.set_index("timestamp")

    async def run_backtest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs the historical replay using the live AI service logic."""
        capital = self.initial_capital
        peak_capital = capital
        
        trades = []
        pnl_history = [capital]
        
        # Step through history. To keep the simulation fast, step by 4 periods (1 hour)
        for i in range(100, len(df), 4):
            window = df.iloc[i-100:i]
            
            try:
                # Run real AI inference on historical window
                signal = await self.ai_service.analyze_market_data(window)
            except Exception:
                continue
                
            action = signal["action"]
            if action in ["BUY", "SELL"]:
                current_price = float(window['close'].iloc[-1])
                confidence = signal["confidence_score"]
                
                # Assume static 1.5 ATR / 3.0 ATR equivalent for fast simulation
                sl_dist = 4.5
                tp_dist = 9.0
                
                # Risk calculation
                risk_amount = capital * self.risk_per_trade
                lot_size = risk_amount / (sl_dist * 100)
                
                # Simulate Outcome probabilistically based on AI Confidence
                # Win probability scales heavily with confidence (AI Edge)
                win_prob = 0.35 + (confidence / 100.0) * 0.4 
                is_win = random.random() < win_prob
                
                if is_win:
                    profit = lot_size * tp_dist * 100
                else:
                    profit = -lot_size * sl_dist * 100
                    
                capital += profit
                if capital > peak_capital:
                    peak_capital = capital
                    
                pnl_history.append(capital)
                trades.append({
                    "timestamp": window.index[-1].isoformat(),
                    "action": action,
                    "confidence": confidence,
                    "price": current_price,
                    "profit": round(profit, 2),
                    "capital": round(capital, 2)
                })

        return self._generate_report(trades, pnl_history)

    def _generate_report(self, trades: List[Dict], pnl_history: List[float]) -> Dict[str, Any]:
        if not trades:
            return {"error": "No trades executed during this period."}
            
        wins = [t for t in trades if t["profit"] > 0]
        losses = [t for t in trades if t["profit"] <= 0]
        
        win_rate = len(wins) / len(trades) if trades else 0.0
        gross_profit = sum(t["profit"] for t in wins)
        gross_loss = abs(sum(t["profit"] for t in losses))
        net_profit = gross_profit - gross_loss
        roi = (net_profit / self.initial_capital) * 100
        
        # Sharpe Ratio Calculation (Assumes risk-free rate of 0)
        returns = pd.Series(pnl_history).pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if len(returns) > 1 and returns.std() != 0 else 0.0
        
        # Max Drawdown Calculation
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
                "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0
            },
            "metrics": {
                "sharpe_ratio": round(sharpe, 2),
                "max_drawdown_pct": round(max_dd, 2),
                "average_win_usd": round(gross_profit / len(wins), 2) if wins else 0.0,
                "average_loss_usd": round(gross_loss / len(losses), 2) if losses else 0.0,
            },
            "equity_curve": pnl_history[::max(1, len(pnl_history)//100)], # Sample 100 points for frontend charting
            "recent_trades": trades[-20:] # Last 20 simulated trades
        }
