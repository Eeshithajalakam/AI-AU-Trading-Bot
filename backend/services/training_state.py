"""In-memory training progress for WebSocket broadcasts."""

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock


@dataclass
class TrainingProgress:
    job_id: int | None = None
    status: str = "idle"
    progress_pct: float = 0.0
    current_epoch: int = 0
    total_epochs: int = 0
    train_loss: float | None = None
    val_mae: float | None = None
    val_rmse: float | None = None
    directional_accuracy: float | None = None
    message: str = ""
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress_pct": round(self.progress_pct, 2),
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "train_loss": self.train_loss,
            "val_mae": self.val_mae,
            "val_rmse": self.val_rmse,
            "directional_accuracy": self.directional_accuracy,
            "message": self.message,
            "updated_at": self.updated_at,
        }


class TrainingStateManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state = TrainingProgress()

    def update(self, **kwargs) -> TrainingProgress:
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self._state, k):
                    setattr(self._state, k, v)
            self._state.updated_at = datetime.utcnow().isoformat()
            return self._state

    def get(self) -> TrainingProgress:
        with self._lock:
            return self._state

    def reset(self) -> None:
        with self._lock:
            self._state = TrainingProgress()


training_state = TrainingStateManager()
