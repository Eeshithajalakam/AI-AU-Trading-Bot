"""LSTM training pipeline with validation metrics (CPU-optimized)."""

import logging
import os
from pathlib import Path
from typing import Callable

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

from ai.indicators import compute_all_indicators
from ai.lstm_model import XAUPredictorLSTM
from ai.constants import FEATURE_COLUMNS, SEQUENCE_LENGTH
from core.config import settings

logger = logging.getLogger(__name__)

# CPU thread optimization
torch.set_num_threads(max(1, os.cpu_count() or 4))


def prepare_dataset(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
    enriched = compute_all_indicators(df)
    features = enriched[FEATURE_COLUMNS].values
    close_idx = FEATURE_COLUMNS.index("close")

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(features)

    X, y, raw_close = [], [], []
    for i in range(SEQUENCE_LENGTH, len(scaled)):
        X.append(scaled[i - SEQUENCE_LENGTH : i])
        y.append(scaled[i, close_idx])
        raw_close.append(float(enriched["close"].iloc[i]))

    X = np.array(X)
    y = np.array(y)
    raw_close = np.array(raw_close)

    split = int(len(X) * train_ratio)
    if split < 30 or len(X) - split < 10:
        raise ValueError(f"Insufficient samples after split: {len(X)} total")

    return X[:split], y[:split], X[split:], y[split:], scaler, raw_close[split:]


def _compute_metrics(
    model: XAUPredictorLSTM,
    X_val: np.ndarray,
    y_val: np.ndarray,
    raw_close_val: np.ndarray,
    scaler: MinMaxScaler,
    device: torch.device,
) -> dict:
    model.eval()
    close_idx = FEATURE_COLUMNS.index("close")

    with torch.no_grad():
        preds_scaled = model(torch.FloatTensor(X_val).to(device)).cpu().numpy().flatten()

    # Unscale predictions and actuals
    def unscale_close(vals: np.ndarray) -> np.ndarray:
        dummy = np.zeros((len(vals), len(FEATURE_COLUMNS)))
        dummy[:, close_idx] = vals
        return scaler.inverse_transform(dummy)[:, close_idx]

    y_actual = unscale_close(y_val)
    y_pred = unscale_close(preds_scaled)

    mae = float(np.mean(np.abs(y_actual - y_pred)))
    rmse = float(np.sqrt(np.mean((y_actual - y_pred) ** 2)))

    # Directional accuracy: did we predict up/down correctly?
    if len(raw_close_val) > 1:
        actual_dir = np.sign(np.diff(raw_close_val))
        pred_dir = np.sign(np.diff(y_pred[: len(actual_dir)]))
        directional_accuracy = float(np.mean(actual_dir == pred_dir) * 100)
    else:
        directional_accuracy = 0.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "directional_accuracy": round(directional_accuracy, 2),
    }


def train_model(
    df: pd.DataFrame,
    epochs: int = 25,
    learning_rate: float = 0.001,
    batch_size: int = 32,
    save: bool = True,
    progress_callback: Callable[[dict], None] | None = None,
    job_id: int | None = None,
) -> dict:
    """
    Synchronous training function — call via asyncio.to_thread from async code.
    """
    X_train, y_train, X_val, y_val, scaler, raw_close_val = prepare_dataset(df)

    device = torch.device("cpu")
    model = XAUPredictorLSTM(input_size=len(FEATURE_COLUMNS)).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    train_loader = DataLoader(
        TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train).unsqueeze(1),
        ),
        batch_size=batch_size,
        shuffle=True,
    )

    losses = []
    model.train()

    for epoch in range(epochs):
        epoch_losses = []
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            epoch_losses.append(loss.item())

        avg_loss = float(np.mean(epoch_losses))
        losses.append(avg_loss)
        progress_pct = ((epoch + 1) / epochs) * 100

        metrics = _compute_metrics(model, X_val, y_val, raw_close_val, scaler, device)

        log_msg = (
            f"Epoch {epoch + 1}/{epochs} | loss={avg_loss:.6f} | "
            f"MAE={metrics['mae']} | RMSE={metrics['rmse']} | "
            f"DirAcc={metrics['directional_accuracy']}%"
        )
        logger.info(log_msg)

        if progress_callback:
            progress_callback({
                "job_id": job_id,
                "status": "running",
                "progress_pct": progress_pct,
                "current_epoch": epoch + 1,
                "total_epochs": epochs,
                "train_loss": avg_loss,
                "val_mae": metrics["mae"],
                "val_rmse": metrics["rmse"],
                "directional_accuracy": metrics["directional_accuracy"],
                "message": log_msg,
            })

    final_metrics = _compute_metrics(model, X_val, y_val, raw_close_val, scaler, device)
    model.eval()

    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    model_path = settings.resolved_model_path
    scaler_path = settings.scaler_path

    if save:
        torch.save(model.state_dict(), model_path)
        joblib.dump(scaler, scaler_path)
        meta = {
            "feature_columns": FEATURE_COLUMNS,
            "sequence_length": SEQUENCE_LENGTH,
            "epochs": epochs,
            "final_loss": losses[-1],
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            **final_metrics,
        }
        joblib.dump(meta, str(Path(settings.MODEL_DIR) / "model_meta.pkl"))
        logger.info("Model saved to %s | MAE=%s RMSE=%s DirAcc=%s%%",
                    model_path, final_metrics["mae"], final_metrics["rmse"],
                    final_metrics["directional_accuracy"])

    result = {
        "status": "trained",
        "job_id": job_id,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "epochs": epochs,
        "final_loss": round(losses[-1], 6),
        "model_path": model_path,
        "device": str(device),
        "metrics": final_metrics,
    }

    if progress_callback:
        progress_callback({
            "job_id": job_id,
            "status": "completed",
            "progress_pct": 100.0,
            "current_epoch": epochs,
            "total_epochs": epochs,
            "train_loss": losses[-1],
            **{f"val_{k}" if k in ("mae", "rmse") else k: v for k, v in final_metrics.items()},
            "val_mae": final_metrics["mae"],
            "val_rmse": final_metrics["rmse"],
            "directional_accuracy": final_metrics["directional_accuracy"],
            "message": "Training completed successfully",
            "meta": result,
        })

    return result
