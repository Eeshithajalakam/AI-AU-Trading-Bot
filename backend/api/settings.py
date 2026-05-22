from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.deps import order_manager
from core.database import AsyncSessionLocal
from db.repository import SettingsRepository

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class RiskSettings(BaseModel):
    max_daily_drawdown_pct: float
    max_trade_risk_pct: float
    max_daily_trades: int
    emergency_shutdown: bool


@router.get("/risk")
async def get_risk_settings():
    engine = order_manager.risk_engine
    stored = {}
    try:
        async with AsyncSessionLocal() as session:
            stored = await SettingsRepository.get(session, "risk", {})
    except Exception:
        pass
    return {
        "max_daily_drawdown_pct": round(engine.max_daily_drawdown_pct * 100, 2),
        "max_trade_risk_pct": round(engine.max_trade_risk_pct * 100, 2),
        "max_daily_trades": engine.max_daily_trades,
        "emergency_shutdown": engine.emergency_shutdown,
        "stored": stored,
    }


@router.post("/risk")
async def update_risk_settings(settings: RiskSettings):
    engine = order_manager.risk_engine
    if settings.max_daily_drawdown_pct <= 0 or settings.max_daily_drawdown_pct > 20:
        raise HTTPException(status_code=400, detail="Daily drawdown must be between 0.1% and 20%")
    if settings.max_trade_risk_pct <= 0 or settings.max_trade_risk_pct > 10:
        raise HTTPException(status_code=400, detail="Trade risk must be between 0.1% and 10%")

    engine.max_daily_drawdown_pct = settings.max_daily_drawdown_pct / 100.0
    engine.max_trade_risk_pct = settings.max_trade_risk_pct / 100.0
    engine.max_daily_trades = settings.max_daily_trades

    if engine.emergency_shutdown and not settings.emergency_shutdown:
        engine.current_daily_pnl = 0.0
        engine.daily_trades = 0

    engine.emergency_shutdown = settings.emergency_shutdown

    payload = settings.model_dump()
    try:
        async with AsyncSessionLocal() as session:
            await SettingsRepository.upsert(session, "risk", payload)
    except Exception:
        pass

    return {"status": "success", "message": "Risk parameters updated successfully."}
