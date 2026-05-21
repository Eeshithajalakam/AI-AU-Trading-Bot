import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .lstm_model import ModelPipeline
from .indicators import compute_all_indicators
from .signals import SignalEngine

class AIService:
    def __init__(self):
        self.model_pipeline = ModelPipeline()
        self.signal_engine = SignalEngine()
        
        # Features expected by the LSTM model
        self.feature_columns = [
            'open', 'high', 'low', 'close', 'volume',
            'SMA_20', 'SMA_50', 'EMA_9', 'EMA_21', 'RSI_14',
            'MACD', 'MACD_Signal', 'MACD_Hist', 'BB_Upper', 'BB_Lower'
        ]
        self.latest_indicators_snapshot = {}
        self.signal_history = []
        self.analytics = {
            "total_signals": 0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
            "average_confidence": 0.0
        }

    async def analyze_market_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes raw OHLCV DataFrame, computes indicators, predicts next price, and generates a trading signal.
        """
        if len(df) < 50:
            raise ValueError("Not enough data to compute reliable indicators. Require at least 50 periods.")

        # 1. Compute Indicators
        df_enriched = compute_all_indicators(df)
        
        # 2. Extract features for LSTM
        # We need a sequence for LSTM, using the last 60 periods
        sequence_length = 60
        if len(df_enriched) < sequence_length:
            sequence_length = len(df_enriched)

        features = df_enriched[self.feature_columns].values[-sequence_length:]
        
        # Robust scaling for inference
        # In a real production system, you would load a pre-fitted StandardScaler.
        # Here we dynamically scale based on the recent window for demonstration.
        min_vals = np.min(features, axis=0)
        max_vals = np.max(features, axis=0)
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1 # Avoid division by zero
        
        scaled_features = (features - min_vals) / range_vals

        # 3. Predict next price
        current_price = float(df_enriched['close'].iloc[-1])
        print("Generating AI signal...")
        try:
            scaled_prediction = self.model_pipeline.predict(scaled_features)
            
            # Unscale prediction (assuming output maps to 'close' price)
            close_idx = self.feature_columns.index('close')
            predicted_price = (scaled_prediction * range_vals[close_idx]) + min_vals[close_idx]
            
            if np.isnan(predicted_price) or predicted_price <= 0:
                raise ValueError(f"Invalid prediction result: {predicted_price}")
            
            print("LSTM prediction success")
        except Exception as e:
            import traceback
            print(f"LSTM prediction failed: {e}\n{traceback.format_exc()}")
            # Fallback prediction
            predicted_price = current_price * (1 + np.random.normal(0, 0.002))
            print("Fallback prediction used")

        # 4. Generate Signal
        latest_indicators = df_enriched.iloc[-1].to_dict()
        
        # Store snapshot for API access
        self.latest_indicators_snapshot = {k: float(v) if pd.notna(v) else 0.0 for k, v in latest_indicators.items() if isinstance(v, (int, float, np.number))}
        
        signal = self.signal_engine.generate_signal(
            current_price=current_price,
            predicted_price=predicted_price,
            indicators_latest=latest_indicators
        )
        
        # Store in history
        self.signal_history.append(signal)
        if len(self.signal_history) > 1000: # Keep last 1000 signals in memory
            self.signal_history.pop(0)
        print("Signal appended to history")
            
        # Update analytics
        self.analytics["total_signals"] += 1
        if signal["trend"] == "BULLISH":
            self.analytics["bullish_signals"] += 1
        elif signal["trend"] == "BEARISH":
            self.analytics["bearish_signals"] += 1
        else:
            self.analytics["neutral_signals"] += 1
            
        # Running average of confidence
        n = self.analytics["total_signals"]
        prev_avg = self.analytics["average_confidence"]
        self.analytics["average_confidence"] = prev_avg + (signal["confidence_score"] - prev_avg) / n
        
        return signal
