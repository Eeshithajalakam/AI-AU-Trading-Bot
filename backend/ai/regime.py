"""Market regime and anomaly detection for XAU/USD."""

from typing import Any

import numpy as np
import pandas as pd


def detect_regime(df: pd.DataFrame) -> dict[str, Any]:
    if len(df) < 30:
        return {"regime": "unknown", "volatility": "normal", "trend_strength": 0.0}

    close = df["close"]
    returns = close.pct_change().dropna()
    atr = df["ATR_14"].iloc[-1] if "ATR_14" in df.columns else close.diff().abs().rolling(14).mean().iloc[-1]
    atr_pct = (atr / close.iloc[-1]) * 100 if close.iloc[-1] else 0

    # Trend: ADX proxy via EMA slope
    ema = df["EMA_20"].iloc[-1] if "EMA_20" in df.columns else close.ewm(span=20).mean().iloc[-1]
    ema_prev = df["EMA_20"].iloc[-10] if "EMA_20" in df.columns else close.ewm(span=20).mean().iloc[-10]
    trend_strength = abs((ema - ema_prev) / ema_prev) * 100 if ema_prev else 0

    vol_std = returns.tail(20).std() * np.sqrt(252) * 100 if len(returns) >= 5 else 0

    if atr_pct > 0.35 or vol_std > 25:
        volatility = "high"
    elif atr_pct < 0.12:
        volatility = "low"
    else:
        volatility = "normal"

    if trend_strength > 0.15:
        regime = "trending"
    elif volatility == "high":
        regime = "high_volatility"
    else:
        regime = "ranging"

    # Anomaly: z-score of last return
    last_ret = returns.iloc[-1] if len(returns) else 0
    z = 0.0
    if len(returns) > 10 and returns.std() > 0:
        z = (last_ret - returns.mean()) / returns.std()
    anomaly = abs(z) > 2.5

    return {
        "regime": regime,
        "volatility": volatility,
        "trend_strength": round(trend_strength, 4),
        "atr_pct": round(atr_pct, 4),
        "anomaly_detected": bool(anomaly),
        "return_zscore": round(float(z), 3),
    }
