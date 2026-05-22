import logging
from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn as nn

from ai.constants import FEATURE_COLUMNS, SEQUENCE_LENGTH

logger = logging.getLogger(__name__)


class XAUPredictorLSTM(nn.Module):
    def __init__(
        self,
        input_size: int = 15,
        hidden_layer_size: int = 64,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size,
            hidden_layer_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.linear = nn.Linear(hidden_layer_size, output_size)

    def forward(self, input_seq: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(input_seq)
        return self.linear(lstm_out[:, -1, :])


class ModelPipeline:
    def __init__(self, model_path: str | None = None, scaler_path: str | None = None):
        self.input_size = len(FEATURE_COLUMNS)
        self.sequence_length = SEQUENCE_LENGTH
        self.feature_columns = FEATURE_COLUMNS
        self.model = XAUPredictorLSTM(input_size=self.input_size)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.scaler = None
        self.model_loaded = False

        if model_path and Path(model_path).exists():
            self.load_model(model_path, scaler_path)
        else:
            self.model.eval()
            logger.warning("No trained model found at %s — using untrained weights", model_path)

    def load_model(self, path: str, scaler_path: str | None = None) -> bool:
        try:
            try:
                state = torch.load(path, map_location=self.device, weights_only=True)
            except TypeError:
                state = torch.load(path, map_location=self.device)
            self.model.load_state_dict(state)
            self.model.eval()
            self.model_loaded = True
            if scaler_path and Path(scaler_path).exists():
                self.scaler = joblib.load(scaler_path)
            logger.info("Loaded LSTM model from %s", path)
            return True
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            return False

    def predict(self, features: np.ndarray) -> float:
        if features.shape[-1] != self.input_size:
            raise ValueError(f"Expected {self.input_size} features, got {features.shape[-1]}")

        if self.scaler is not None:
            scaled = self.scaler.transform(features)
        else:
            min_vals = np.min(features, axis=0)
            max_vals = np.max(features, axis=0)
            range_vals = max_vals - min_vals
            range_vals[range_vals == 0] = 1
            scaled = (features - min_vals) / range_vals

        with torch.no_grad():
            seq_tensor = torch.FloatTensor(scaled[-self.sequence_length :]).unsqueeze(0).to(self.device)
            prediction = self.model(seq_tensor)
            scaled_pred = prediction.item()

        if self.scaler is not None:
            close_idx = self.feature_columns.index("close")
            dummy = np.zeros((1, self.input_size))
            dummy[0, close_idx] = scaled_pred
            unscaled = self.scaler.inverse_transform(dummy)
            return float(unscaled[0, close_idx])

        close_idx = self.feature_columns.index("close")
        min_vals = np.min(features, axis=0)
        max_vals = np.max(features, axis=0)
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1
        return float(scaled_pred * range_vals[close_idx] + min_vals[close_idx])
