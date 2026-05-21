from fastapi import APIRouter, HTTPException
from api.websockets import ai_service
import datetime

router = APIRouter(prefix="/api/indicators", tags=["Indicators"])

@router.get("/xauusd")
async def get_xauusd_indicators():
    """
    Returns the latest technical indicator snapshot for XAU/USD.
    Used for frontend dashboard visualization (TradingView-style).
    """
    snapshot = ai_service.latest_indicators_snapshot
    
    if not snapshot:
        # If the websocket loop hasn't run yet or no data
        return {
            "status": "waiting",
            "message": "Indicators are still calculating. Please wait a few seconds."
        }
        
    return {
        "asset": "XAU/USD",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "indicators": snapshot
    }
