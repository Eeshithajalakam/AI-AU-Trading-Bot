"""Background training orchestration with DB + progress state."""

import asyncio
import logging
from datetime import datetime, timezone

from ai.trainer import train_model
from core.config import settings
from core.database import AsyncSessionLocal
from core.deps import ai_service
from db.repository import TrainingRepository
from services.market_engine import market_engine
from services.training_state import training_state

logger = logging.getLogger(__name__)


def _on_progress(data: dict) -> None:
    training_state.update(
        job_id=data.get("job_id"),
        status=data.get("status", "running"),
        progress_pct=data.get("progress_pct", 0),
        current_epoch=data.get("current_epoch", 0),
        total_epochs=data.get("total_epochs", 0),
        train_loss=data.get("train_loss"),
        val_mae=data.get("val_mae"),
        val_rmse=data.get("val_rmse"),
        directional_accuracy=data.get("directional_accuracy"),
        message=data.get("message", ""),
    )


async def _update_db_job(job_id: int, **kwargs) -> None:
    try:
        async with AsyncSessionLocal() as session:
            await TrainingRepository.update_job(session, job_id, **kwargs)
    except Exception as e:
        logger.warning("Training job DB update failed: %s", e)


async def run_training(epochs: int = 25, period: str = "60d") -> dict:
    training_state.update(status="starting", message="Fetching historical data...", progress_pct=0)

    job_id: int | None = None
    try:
        async with AsyncSessionLocal() as session:
            job = await TrainingRepository.create_job(session, epochs)
            job_id = job.id
    except Exception as e:
        logger.warning("Could not create training job in DB: %s", e)

    training_state.update(job_id=job_id, status="running", total_epochs=epochs)

    try:
        df = await market_engine.fetch_historical(period=period)
        df = df.set_index("timestamp")

        loop = asyncio.get_running_loop()

        def progress_cb(data: dict) -> None:
            data["job_id"] = job_id
            _on_progress(data)
            if job_id and data.get("status") in ("running", "completed", "failed"):
                asyncio.run_coroutine_threadsafe(
                    _update_db_job(
                        job_id,
                        status=data.get("status", "running"),
                        progress_pct=data.get("progress_pct", 0),
                        current_epoch=data.get("current_epoch", 0),
                        train_loss=data.get("train_loss"),
                        val_mae=data.get("val_mae"),
                        val_rmse=data.get("val_rmse"),
                        directional_accuracy=data.get("directional_accuracy"),
                        message=data.get("message"),
                        finished_at=datetime.now(timezone.utc) if data.get("status") == "completed" else None,
                        meta=data.get("meta"),
                    ),
                    loop,
                )

        result = await asyncio.to_thread(
            train_model, df, epochs, 0.001, 32, True, progress_cb, job_id
        )

        ai_service.model_pipeline.load_model(
            settings.resolved_model_path, settings.scaler_path
        )
        training_state.update(status="completed", progress_pct=100, message="Model loaded for inference")
        return result
    except Exception as e:
        logger.exception("Training failed")
        training_state.update(status="failed", message=str(e))
        if job_id:
            await _update_db_job(job_id, status="failed", message=str(e))
        raise
