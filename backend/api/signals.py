from fastapi import APIRouter
from api.websockets import ai_service

router = APIRouter(prefix="/api/signals", tags=["Signals"])

@router.get("/xauusd")
async def get_latest_signal():
    """
    Get the most recently generated AI signal for XAU/USD.
    """
    if not ai_service.signal_history:
        return {"status": "waiting", "message": "No signals generated yet. Please wait."}
    return ai_service.signal_history[-1]

@router.get("/history")
async def get_signal_history(limit: int = 50):
    """
    Get a list of the historical signals generated.
    """
    if not ai_service.signal_history:
        return []
    return ai_service.signal_history[-limit:]
