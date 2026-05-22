import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from core.config import settings
from core.deps import ai_service
from core.database import AsyncSessionLocal
from db.repository import TrainingRepository
from services.training_runner import run_training, training_state
from services.training_state import training_state as ts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training", tags=["Training"])

_training_lock = asyncio.Lock()
_training_task: asyncio.Task | None = None


async def _run_training_task(epochs: int, period: str) -> None:
    async with _training_lock:
        try:
            await run_training(epochs=epochs, period=period)
        except Exception as e:
            logger.error("Background training error: %s", e)


@router.post("/train")
async def train_lstm(
    background_tasks: BackgroundTasks,
    period: str = Query("60d"),
    epochs: int = Query(25, ge=5, le=200),
    background: bool = Query(True, description="Run training in background"),
):
    global _training_task
    state = ts.get()
    if state.status == "running":
        raise HTTPException(status_code=409, detail="Training already in progress")

    if background:
        _training_task = asyncio.create_task(_run_training_task(epochs, period))
        return {"status": "started", "message": "Training started in background", "epochs": epochs}

    try:
        return await run_training(epochs=epochs, period=period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def training_status():
    state = ts.get().to_dict()
    model_exists = Path(settings.resolved_model_path).exists()
    db_job = None
    try:
        async with AsyncSessionLocal() as session:
            job = await TrainingRepository.get_latest(session)
            if job:
                db_job = {
                    "id": job.id,
                    "status": job.status,
                    "progress_pct": job.progress_pct,
                    "val_mae": job.val_mae,
                    "val_rmse": job.val_rmse,
                    "directional_accuracy": job.directional_accuracy,
                    "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                }
    except Exception:
        pass

    return {
        "live": state,
        "db_job": db_job,
        "model_loaded": ai_service.model_pipeline.model_loaded,
        "model_file_exists": model_exists,
        "model_path": settings.resolved_model_path,
        "device": str(ai_service.model_pipeline.device),
    }


@router.get("/metrics")
async def training_metrics():
    meta_path = Path(settings.MODEL_DIR) / "model_meta.pkl"
    if not meta_path.exists():
        return {"status": "no_model", "message": "Train model first"}
    import joblib
    meta = joblib.load(meta_path)
    return {"status": "ok", "metrics": meta}
