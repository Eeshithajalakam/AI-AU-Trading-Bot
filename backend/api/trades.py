from fastapi import APIRouter, Query
from core.database import AsyncSessionLocal
from db.repository import TradeRepository
import json
import os

router = APIRouter(prefix="/api/trades", tags=["Trades"])
TRADE_LOG_FILE = "trade_logs.json"


def _trade_to_dict(t) -> dict:
    return {
        "id": t.id,
        "signal_id": t.signal_id,
        "symbol": t.symbol,
        "action": t.action,
        "volume": t.volume,
        "entry_price": t.entry_price,
        "sl": t.sl,
        "tp": t.tp,
        "pnl": t.pnl,
        "status": t.status,
        "paper_trade": t.paper_trade,
        "mt5_ticket": t.mt5_ticket,
        "details": t.details,
        "timestamp": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/history")
async def get_trade_history(limit: int = Query(50, le=200)):
    try:
        async with AsyncSessionLocal() as session:
            trades = await TradeRepository.list_recent(session, limit)
            if trades:
                return [_trade_to_dict(t) for t in trades]
    except Exception:
        pass

    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, "r") as f:
            logs = json.load(f)
        return logs[-limit:][::-1]
    return []


@router.get("/pnl")
async def get_daily_pnl():
    try:
        async with AsyncSessionLocal() as session:
            pnl = await TradeRepository.daily_pnl(session)
            open_count = await TradeRepository.open_trade_count(session)
            return {"daily_pnl": round(pnl, 2), "open_trades": open_count}
    except Exception:
        from core.deps import order_manager
        return {
            "daily_pnl": round(order_manager.risk_engine.current_daily_pnl, 2),
            "open_trades": 0,
        }
