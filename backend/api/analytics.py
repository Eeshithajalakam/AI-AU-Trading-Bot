from fastapi import APIRouter
from core.deps import ai_service, order_manager
from core.database import AsyncSessionLocal
from db.repository import AnalyticsRepository, TradeRepository

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
async def get_analytics():
    analytics = dict(ai_service.analytics)
    daily_pnl = 0.0
    open_trades = 0
    db_snapshot = None

    try:
        async with AsyncSessionLocal() as session:
            daily_pnl = await TradeRepository.daily_pnl(session)
            open_trades = await TradeRepository.open_trade_count(session)
            snap = await AnalyticsRepository.get_latest(session)
            if snap:
                db_snapshot = {
                    "total_signals": snap.total_signals,
                    "average_confidence": snap.average_confidence,
                    "daily_pnl": snap.daily_pnl,
                    "recorded_at": snap.created_at.isoformat(),
                }
    except Exception:
        daily_pnl = order_manager.risk_engine.current_daily_pnl

    account = order_manager.broker.get_account_info()
    return {
        "asset": "XAU/USD",
        "analytics": analytics,
        "daily_pnl": round(daily_pnl, 2),
        "open_trades": open_trades,
        "account": account,
        "db_snapshot": db_snapshot,
        "latest_signal": ai_service.signal_history[-1] if ai_service.signal_history else None,
        "risk": {
            "emergency_shutdown": order_manager.risk_engine.emergency_shutdown,
            "daily_trades": order_manager.risk_engine.daily_trades,
            "max_daily_trades": order_manager.risk_engine.max_daily_trades,
        },
    }
