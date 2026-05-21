from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.websockets import order_manager

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class RiskSettings(BaseModel):
    max_daily_drawdown_pct: float
    max_trade_risk_pct: float
    max_daily_trades: int
    emergency_shutdown: bool

@router.get("/risk")
async def get_risk_settings():
    """Retrieve the current live risk parameters from the Risk Engine."""
    engine = order_manager.risk_engine
    return {
        "max_daily_drawdown_pct": round(engine.max_daily_drawdown_pct * 100, 2),
        "max_trade_risk_pct": round(engine.max_trade_risk_pct * 100, 2),
        "max_daily_trades": engine.max_daily_trades,
        "emergency_shutdown": engine.emergency_shutdown
    }

@router.post("/risk")
async def update_risk_settings(settings: RiskSettings):
    """Dynamically update the Risk Engine parameters in real-time."""
    engine = order_manager.risk_engine
    
    # Validation
    if settings.max_daily_drawdown_pct <= 0 or settings.max_daily_drawdown_pct > 20:
        raise HTTPException(status_code=400, detail="Daily drawdown must be between 0.1% and 20%")
    if settings.max_trade_risk_pct <= 0 or settings.max_trade_risk_pct > 10:
        raise HTTPException(status_code=400, detail="Trade risk must be between 0.1% and 10%")
        
    # Apply Updates
    engine.max_daily_drawdown_pct = settings.max_daily_drawdown_pct / 100.0
    engine.max_trade_risk_pct = settings.max_trade_risk_pct / 100.0
    engine.max_daily_trades = settings.max_daily_trades
    
    # If un-toggling emergency shutdown, reset daily PnL conditionally or just un-toggle
    if engine.emergency_shutdown and not settings.emergency_shutdown:
        # Reset daily PnL & trades to allow trading to resume immediately
        engine.current_daily_pnl = 0.0
        engine.daily_trades = 0
        
    engine.emergency_shutdown = settings.emergency_shutdown
    
    return {"status": "success", "message": "Institutional risk parameters updated successfully."}
