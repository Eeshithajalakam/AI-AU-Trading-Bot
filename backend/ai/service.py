import logging
from typing import Any

import numpy as np
import pandas as pd

from ai.lstm_model import ModelPipeline
from ai.indicators import compute_all_indicators
from ai.signals import SignalEngine
from ai.constants import FEATURE_COLUMNS, SEQUENCE_LENGTH
from core.config import settings
from services.market_engine import market_engine

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self) -> None:
        self.model_pipeline = ModelPipeline(
            model_path=settings.resolved_model_path,
            scaler_path=settings.scaler_path,
        )
        self.signal_engine = SignalEngine()
        self.feature_columns = FEATURE_COLUMNS
        self.sequence_length = SEQUENCE_LENGTH
        self.latest_indicators_snapshot: dict[str, float] = {}
        self.signal_history: list[dict[str, Any]] = []
        self.analytics = {
            "total_signals": 0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
            "average_confidence": 0.0,
        }

    async def analyze_market_data(self, df: pd.DataFrame) -> dict[str, Any]:
        if len(df) < 50:
            raise ValueError("Not enough data to compute reliable indicators. Require at least 50 periods.")

        df_enriched = compute_all_indicators(df)
        seq_len = min(self.sequence_length, len(df_enriched))
        features = df_enriched[self.feature_columns].values[-seq_len:]
        current_price = float(df_enriched["close"].iloc[-1])

        try:
            predicted_price = self.model_pipeline.predict(features)
            if np.isnan(predicted_price) or predicted_price <= 0:
                raise ValueError(f"Invalid prediction: {predicted_price}")
        except Exception as e:
            logger.warning("LSTM prediction failed (%s), using momentum fallback", e)
            momentum = float(df_enriched["close"].pct_change(5).iloc[-1] or 0)
            predicted_price = current_price * (1 + momentum * 0.5)

        latest_indicators = df_enriched.iloc[-1].to_dict()
        self.latest_indicators_snapshot = {
            k: float(v) if pd.notna(v) else 0.0
            for k, v in latest_indicators.items()
            if isinstance(v, (int, float, np.number))
        }

        mtf = market_engine.get_multi_timeframe_summary()
        signal = self.signal_engine.generate_signal(
            current_price=current_price,
            predicted_price=predicted_price,
            indicators_latest=latest_indicators,
            df=df_enriched,
            mtf_summary=mtf,
        )

        self.signal_history.append(signal)
        if len(self.signal_history) > 1000:
            self.signal_history.pop(0)

        self.analytics["total_signals"] += 1
        if signal["trend"] == "BULLISH":
            self.analytics["bullish_signals"] += 1
        elif signal["trend"] == "BEARISH":
            self.analytics["bearish_signals"] += 1
        else:
            self.analytics["neutral_signals"] += 1

        n = self.analytics["total_signals"]
        prev_avg = self.analytics["average_confidence"]
        self.analytics["average_confidence"] = prev_avg + (signal["confidence_score"] - prev_avg) / n

        return signal
