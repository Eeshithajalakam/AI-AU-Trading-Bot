from typing import Any

import numpy as np
import pandas as pd

from ai.regime import detect_regime


class SignalEngine:
    def __init__(self) -> None:
        self.trend_threshold = 0.0004

    def generate_signal(
        self,
        current_price: float,
        predicted_price: float,
        indicators_latest: dict[str, float],
        df: pd.DataFrame | None = None,
        mtf_summary: dict | None = None,
    ) -> dict[str, Any]:
        price_diff_pct = (predicted_price - current_price) / current_price if current_price else 0

        if price_diff_pct > self.trend_threshold:
            ai_trend, ai_score = "BULLISH", min(price_diff_pct / (self.trend_threshold * 3), 1.0) * 100
        elif price_diff_pct < -self.trend_threshold:
            ai_trend, ai_score = "BEARISH", min(abs(price_diff_pct) / (self.trend_threshold * 3), 1.0) * 100
        else:
            ai_trend, ai_score = "NEUTRAL", 50.0

        regime_info = detect_regime(df) if df is not None and len(df) >= 30 else {
            "regime": "unknown", "volatility": "normal", "anomaly_detected": False, "trend_strength": 0
        }

        rsi = indicators_latest.get("RSI_14", 50)
        macd_hist = indicators_latest.get("MACD_Hist", 0)
        ema_20 = indicators_latest.get("EMA_20", current_price)
        sma_50 = indicators_latest.get("SMA_50", current_price)
        bb_lower = indicators_latest.get("BB_Lower", current_price * 0.99)
        bb_upper = indicators_latest.get("BB_Upper", current_price * 1.01)
        atr = indicators_latest.get("ATR_14", 3.0)
        vwap = indicators_latest.get("VWAP", current_price)

        ta_score = 0.0
        if rsi < 32:
            ta_score += 1
        elif rsi > 68:
            ta_score -= 1
        if macd_hist > 0:
            ta_score += 1
        elif macd_hist < 0:
            ta_score -= 1
        if current_price > ema_20:
            ta_score += 1
        else:
            ta_score -= 1
        if current_price > sma_50:
            ta_score += 1
        else:
            ta_score -= 1
        if current_price < bb_lower:
            ta_score += 1
        elif current_price > bb_upper:
            ta_score -= 1
        if current_price > vwap:
            ta_score += 0.5
        else:
            ta_score -= 0.5

        # Multi-timeframe confirmation
        mtf_boost = 0.0
        if mtf_summary:
            aligned = 0
            for tf, data in mtf_summary.items():
                ch = data.get("change_pct", 0)
                if ai_trend == "BULLISH" and ch > 0:
                    aligned += 1
                elif ai_trend == "BEARISH" and ch < 0:
                    aligned += 1
            mtf_boost = (aligned / max(len(mtf_summary), 1)) * 15

        ta_normalized = (ta_score / 5.5) * 100

        if regime_info.get("anomaly_detected"):
            action = "HOLD"
            combined_score = 40.0
        elif ai_trend == "BULLISH":
            combined_score = 50 + (ai_score * 0.28) + (ta_normalized * 0.17) + mtf_boost
            action = "BUY" if combined_score > 58 and regime_info["regime"] != "high_volatility" else "HOLD"
        elif ai_trend == "BEARISH":
            combined_score = 50 + (ai_score * 0.28) + (-ta_normalized * 0.17) + mtf_boost
            action = "SELL" if combined_score > 58 and regime_info["regime"] != "high_volatility" else "HOLD"
        else:
            if ta_normalized > 45:
                action, combined_score = "BUY", 55 + ta_normalized * 0.3
            elif ta_normalized < -45:
                action, combined_score = "SELL", 55 + abs(ta_normalized) * 0.3
            else:
                action, combined_score = "HOLD", 50.0

        final_confidence = round(min(max(combined_score, 0), 100.0), 2)
        direction = "UP" if predicted_price > current_price else "DOWN" if predicted_price < current_price else "FLAT"

        sl_dist = atr * 1.5
        tp_dist = atr * 3.0
        rec_sl = round(current_price - sl_dist, 2) if action == "BUY" else round(current_price + sl_dist, 2)
        rec_tp = round(current_price + tp_dist, 2) if action == "BUY" else round(current_price - tp_dist, 2)

        risk_score = round(
            min(100, final_confidence * 0.5 + (20 if regime_info["regime"] == "trending" else 0) + (10 if not regime_info["anomaly_detected"] else -30)),
            1,
        )

        return {
            "timestamp": pd.Timestamp.utcnow().isoformat(),
            "asset": "XAU/USD",
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "predicted_direction": direction,
            "predicted_move_pct": round(price_diff_pct * 100, 4),
            "action": action,
            "trend": ai_trend,
            "confidence_score": final_confidence,
            "risk_score": risk_score,
            "recommended_sl": rec_sl,
            "recommended_tp": rec_tp,
            "regime": regime_info,
            "timeframes_analyzed": list(mtf_summary.keys()) if mtf_summary else ["1m"],
            "metrics": {
                "ai_delta_pct": round(price_diff_pct * 100, 4),
                "rsi": round(rsi, 2),
                "macd_histogram": round(macd_hist, 4),
                "vwap": round(vwap, 2),
                "atr": round(atr, 2),
                "volume_imbalance": round((current_price - vwap) / vwap * 100, 3) if vwap else 0,
                "trend_strength": regime_info.get("trend_strength", 0),
            },
        }
