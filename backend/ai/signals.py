from typing import Dict, Any, List
import pandas as pd
import numpy as np

class SignalEngine:
    def __init__(self):
        self.trend_threshold = 0.0005 # Reduced to 0.05% for more active trading signals
        
    def generate_signal(self, current_price: float, predicted_price: float, indicators_latest: Dict[str, float]) -> Dict[str, Any]:
        """
        Generates a trading signal based on AI prediction and technical indicators.
        """
        price_diff_pct = (predicted_price - current_price) / current_price
        
        # 1. Base AI Trend Prediction
        if price_diff_pct > self.trend_threshold:
            ai_trend = "BULLISH"
            # Scale score up to 100 based on how far past the threshold it is
            ai_score = min(price_diff_pct / (self.trend_threshold * 3), 1.0) * 100
        elif price_diff_pct < -self.trend_threshold:
            ai_trend = "BEARISH"
            ai_score = min(abs(price_diff_pct) / (self.trend_threshold * 3), 1.0) * 100
        else:
            ai_trend = "NEUTRAL"
            ai_score = 50.0

        # 2. Technical Analysis Confluence
        ta_score = 0
        ta_max_score = 7 # Increased max score for new indicators
        
        rsi = indicators_latest.get('RSI_14', 50)
        macd_hist = indicators_latest.get('MACD_Hist', 0)
        ema_20 = indicators_latest.get('EMA_20', current_price)
        sma_50 = indicators_latest.get('SMA_50', current_price)
        bb_lower = indicators_latest.get('BB_Lower', current_price * 0.99)
        bb_upper = indicators_latest.get('BB_Upper', current_price * 1.01)
        vwap = indicators_latest.get('VWAP', current_price)
        fib_382 = indicators_latest.get('Fib_382', current_price)
        fib_618 = indicators_latest.get('Fib_618', current_price)

        # RSI logic
        if rsi < 30: ta_score += 1 # Oversold, bullish signal
        elif rsi > 70: ta_score -= 1 # Overbought, bearish signal

        # MACD logic
        if macd_hist > 0: ta_score += 1
        elif macd_hist < 0: ta_score -= 1

        # EMA/SMA logic
        if current_price > ema_20: ta_score += 1
        else: ta_score -= 1
        
        if current_price > sma_50: ta_score += 1
        else: ta_score -= 1

        # Bollinger Bands logic
        if current_price < bb_lower: ta_score += 1
        elif current_price > bb_upper: ta_score -= 1
        
        # VWAP logic
        if current_price > vwap: ta_score += 1
        else: ta_score -= 1
        
        # Fibonacci bounce logic (simplified)
        # If price is near 61.8% or 38.2% from above, might bounce up
        if fib_618 * 0.998 < current_price < fib_618 * 1.002: ta_score += 0.5
        if fib_382 * 0.998 < current_price < fib_382 * 1.002: ta_score += 0.5

        # Normalize TA Score to -100 to 100
        ta_normalized = (ta_score / ta_max_score) * 100
        
        # 3. Overall Signal Combination
        if ai_trend == "BULLISH":
            # 50 base + up to 30 from AI + up to 20 from TA
            combined_score = 50 + (ai_score * 0.3) + (ta_normalized * 0.2)
            action = "BUY" if combined_score > 55 else "HOLD"
        elif ai_trend == "BEARISH":
            # 50 base + up to 30 from AI + up to 20 from TA
            combined_score = 50 + (ai_score * 0.3) + (-ta_normalized * 0.2)
            action = "SELL" if combined_score > 55 else "HOLD"
        else:
            # If AI is neutral, let strong TA trigger a trade
            if ta_normalized > 40:
                action = "BUY"
                combined_score = 50 + (ta_normalized * 0.5)
            elif ta_normalized < -40:
                action = "SELL"
                combined_score = 50 + (abs(ta_normalized) * 0.5)
            else:
                action = "HOLD"
                combined_score = 50 + (abs(ta_normalized) * 0.2)
                
        final_confidence = round(min(max(combined_score, 0), 100.0), 2)
        print(f"Generated signal: {action} | Confidence: {final_confidence}")

        return {
            "timestamp": pd.Timestamp.utcnow().isoformat(),
            "asset": "XAU/USD",
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "action": action,
            "trend": ai_trend,
            "confidence_score": final_confidence,
            "timeframes_analyzed": ["1m", "5m", "15m", "1H"],
            "metrics": {
                "ai_delta_pct": round(price_diff_pct * 100, 4),
                "rsi": round(rsi, 2),
                "macd_histogram": round(macd_hist, 4),
                "vwap": round(vwap, 2),
                "atr": round(indicators_latest.get('ATR_14', 0), 2)
            }
        }
