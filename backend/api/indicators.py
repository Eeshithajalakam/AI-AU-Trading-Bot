from fastapi import APIRouter
from core.deps import ai_service

router = APIRouter(prefix="/api/indicators", tags=["Indicators"])


@router.get("/xauusd")
async def get_latest_indicators():
    if not ai_service.latest_indicators_snapshot:
        return {"status": "waiting", "message": "Indicators not yet computed."}
    return {
        "asset": "XAU/USD",
        "indicators": ai_service.latest_indicators_snapshot,
    }
