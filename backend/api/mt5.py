from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.deps import order_manager

router = APIRouter(prefix="/api/mt5", tags=["MT5"])


class AccountSwitchRequest(BaseModel):
    mode: str


class ClosePositionRequest(BaseModel):
    ticket: int


@router.post("/switch-account")
async def switch_account(request: AccountSwitchRequest):
    if request.mode not in ("DEMO", "LIVE"):
        raise HTTPException(status_code=400, detail="Mode must be DEMO or LIVE")
    success = order_manager.broker.switch_account(request.mode)
    return {
        "status": "success" if success else "error",
        "mode": request.mode,
        "connected": order_manager.broker.connected,
    }


@router.get("/status")
async def get_mt5_status():
    live = order_manager.get_live_status()
    return {
        "connected": order_manager.broker.connected or settings.PAPER_TRADING_MODE,
        "account_mode": order_manager.broker.account_mode,
        "paper_trading": settings.PAPER_TRADING_MODE,
        "auto_trade_enabled": settings.AUTO_TRADE_ENABLED,
        **live,
    }


@router.get("/account")
async def get_account_dashboard():
    return order_manager.get_live_status()


@router.post("/close-position")
async def close_position(request: ClosePositionRequest):
    import asyncio
    result = await asyncio.to_thread(order_manager.executor.close_position, request.ticket)
    return result


@router.post("/connect")
async def connect_mt5():
    import asyncio
    ok = await asyncio.to_thread(order_manager.broker.connect)
    return {"connected": ok, "paper_mode": settings.PAPER_TRADING_MODE}
