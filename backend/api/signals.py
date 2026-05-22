from fastapi import APIRouter, Query
from core.deps import ai_service
from core.database import AsyncSessionLocal
from db.repository import SignalRepository

router = APIRouter(prefix="/api/signals", tags=["Signals"])


def _signal_to_dict(s) -> dict:
    return {
        "id": s.external_id or str(s.id),
        "asset": s.asset,
        "action": s.action,
        "trend": s.trend,
        "current_price": s.current_price,
        "predicted_price": s.predicted_price,
        "confidence_score": s.confidence_score,
        "metrics": s.metrics,
        "timestamp": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("/xauusd")
async def get_latest_signal():
    try:
        async with AsyncSessionLocal() as session:
            row = await SignalRepository.get_latest(session)
            if row:
                return _signal_to_dict(row)
    except Exception:
        pass
    if ai_service.signal_history:
        return ai_service.signal_history[-1]
    return {"status": "waiting", "message": "No signals yet"}


@router.get("/history")
async def get_signal_history(limit: int = Query(50, le=500)):
    try:
        async with AsyncSessionLocal() as session:
            rows = await SignalRepository.list_recent(session, limit)
            if rows:
                return [_signal_to_dict(s) for s in rows]
    except Exception:
        pass
    return ai_service.signal_history[-limit:]
