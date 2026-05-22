from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import uuid
import logging
from datetime import datetime
from typing import List

from core.config import settings
from core.database import AsyncSessionLocal
from core.deps import ai_service, order_manager
from db.repository import SignalRepository, TradeRepository, AnalyticsRepository
from services.market_engine import market_engine
from services.training_state import training_state

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WS connected (%d clients)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        if not self.active_connections:
            return
        dead: list[WebSocket] = []
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


async def _persist_signal(ai_result: dict) -> None:
    try:
        async with AsyncSessionLocal() as session:
            await SignalRepository.create(session, ai_result)
    except Exception as e:
        logger.debug("Signal persist skipped: %s", e)


async def _persist_trade(trade_record: dict) -> None:
    try:
        async with AsyncSessionLocal() as session:
            await TradeRepository.create(session, trade_record)
    except Exception as e:
        logger.debug("Trade persist skipped: %s", e)


def _build_frontend_signal(ai_result: dict, current_price: float) -> dict:
    action = ai_result["action"]
    signal_type = "LONG" if action == "BUY" else "SHORT" if action == "SELL" else "NEUTRAL"
    sl = ai_result.get("recommended_sl") or (current_price * 0.995 if signal_type == "LONG" else current_price * 1.005)
    tp = ai_result.get("recommended_tp") or ai_result["predicted_price"]
    return {
        "id": f"ai-sig-{uuid.uuid4().hex[:8]}",
        "type": signal_type,
        "action": action,
        "asset": "XAU/USD",
        "confidence": ai_result["confidence_score"],
        "risk_score": ai_result.get("risk_score"),
        "regime": ai_result.get("regime", {}).get("regime"),
        "entry": current_price,
        "target": tp,
        "stopLoss": round(sl, 2),
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "active": action in ("BUY", "SELL"),
        "metrics": ai_result.get("metrics", {}),
        "trend": ai_result.get("trend", "NEUTRAL"),
    }


async def market_data_broadcaster() -> None:
    try:
        await market_engine.bootstrap_history(min_bars=100)
    except Exception as e:
        logger.warning("Market bootstrap failed: %s", e)

    loop_count = 0
    while True:
        try:
            bar = await market_engine.refresh_latest()
            if bar is None:
                market_engine.append_synthetic_tick()

            current_price = market_engine.current_price
            now = datetime.utcnow()

            if manager.active_connections:
                await manager.broadcast(json.dumps({
                    "type": "PRICE_UPDATE",
                    "price": round(current_price, 2),
                    "timestamp": now.isoformat(),
                    "ohlcv": market_engine.ohlcv_for_frontend(1)[-1] if market_engine.history else None,
                }))

                # Training progress stream
                ts = training_state.get()
                if ts.status in ("running", "starting", "completed", "failed"):
                    await manager.broadcast(json.dumps({
                        "type": "TRAINING_UPDATE",
                        "training": ts.to_dict(),
                    }))

                # Risk metrics every 5s
                if loop_count % 5 == 0:
                    account = order_manager.broker.get_account_info()
                    order_manager.risk_engine.sync_equity(
                        account.get("balance", 10000), account.get("equity", 10000)
                    )
                    await manager.broadcast(json.dumps({
                        "type": "RISK_UPDATE",
                        "daily_pnl": order_manager.risk_engine.current_daily_pnl,
                        "daily_trades": order_manager.risk_engine.daily_trades,
                        "emergency_shutdown": order_manager.risk_engine.emergency_shutdown,
                        "risk": order_manager.risk_engine.status_dict(),
                        "account": account,
                        "paper_mode": settings.PAPER_TRADING_MODE,
                        "auto_trade": settings.AUTO_TRADE_ENABLED,
                        "market": market_engine.health_snapshot(),
                    }))

            if loop_count % settings.PREDICTION_INTERVAL_SECONDS == 0:
                df = market_engine.to_dataframe()
                if len(df) >= 50:
                    try:
                        ai_result = await ai_service.analyze_market_data(df)
                        await _persist_signal(ai_result)
                        signal_payload = _build_frontend_signal(ai_result, current_price)

                        if manager.active_connections:
                            await manager.broadcast(json.dumps({
                                "type": "SIGNAL_UPDATE",
                                "signals": [signal_payload],
                            }))

                        if settings.AUTO_TRADE_ENABLED and signal_payload["action"] in ("BUY", "SELL"):
                            trade_result = await asyncio.to_thread(
                                order_manager.process_signal, signal_payload
                            )
                            if trade_result.get("trade_record"):
                                await _persist_trade(trade_result["trade_record"])
                            if manager.active_connections:
                                await manager.broadcast(json.dumps({
                                    "type": "TRADE_UPDATE",
                                    "trade": trade_result,
                                }))
                            logger.info("Auto-trade: %s", trade_result.get("status"))

                        # Periodic analytics snapshot
                        if loop_count % (settings.PREDICTION_INTERVAL_SECONDS * 6) == 0:
                            try:
                                async with AsyncSessionLocal() as session:
                                    await AnalyticsRepository.save_snapshot(session, {
                                        **ai_service.analytics,
                                        "daily_pnl": order_manager.risk_engine.current_daily_pnl,
                                        "open_positions": order_manager.broker.open_position_count(),
                                    })
                            except Exception:
                                pass
                    except Exception:
                        logger.exception("AI analysis error")

            loop_count += 1
        except Exception:
            logger.exception("Broadcaster error")

        await asyncio.sleep(1.0)


@router.websocket("/ws/trading")
async def websocket_trading_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)

    initial_signals = []
    if ai_service.signal_history:
        last = ai_service.signal_history[-1]
        initial_signals = [_build_frontend_signal(last, last["current_price"])]

    await websocket.send_text(json.dumps({
        "type": "INITIAL_DATA",
        "history": market_engine.price_points_for_frontend(120),
        "candles": market_engine.ohlcv_for_frontend(120),
        "signals": initial_signals,
        "price": round(market_engine.current_price, 2),
        "training": training_state.get().to_dict(),
        "account": order_manager.broker.get_account_info(),
    }))

    try:
        while True:
            data = await websocket.receive_text()
            if data in ("ping", '{"type":"ping"}'):
                await websocket.send_text(json.dumps({"type": "PONG", "ts": datetime.utcnow().isoformat()}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(websocket)
