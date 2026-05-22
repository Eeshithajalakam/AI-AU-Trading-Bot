"""Advanced performance analytics API."""

import math
from fastapi import APIRouter, Query
import numpy as np

from core.database import AsyncSessionLocal
from core.deps import order_manager, ai_service
from db.repository import TradeRepository, BacktestRepository

router = APIRouter(prefix="/api/performance", tags=["Performance"])


def _sharpe(returns: list[float], rf: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    arr = np.array(returns)
    std = arr.std()
    if std == 0:
        return 0.0
    return float((arr.mean() - rf) / std * math.sqrt(252))


def _sortino(returns: list[float], rf: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    arr = np.array(returns)
    downside = arr[arr < rf]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float((arr.mean() - rf) / downside.std() * math.sqrt(252))


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    return round(max_dd * 100, 2)


@router.get("/summary")
async def performance_summary():
    trades = []
    try:
        async with AsyncSessionLocal() as session:
            rows = await TradeRepository.list_recent(session, 500)
            trades = [
                {
                    "pnl": r.pnl or 0,
                    "status": r.status,
                    "action": r.action,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
                if r.status == "EXECUTED"
            ]
    except Exception:
        pass

    pnls = [t["pnl"] for t in trades if t.get("pnl") is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0.0

    equity = [10000.0]
    for p in pnls:
        equity.append(equity[-1] + p)

    returns = []
    for i in range(1, len(equity)):
        if equity[i - 1] != 0:
            returns.append((equity[i] - equity[i - 1]) / equity[i - 1])

    account = order_manager.broker.get_account_info()

    return {
        "total_trades": len(pnls),
        "win_rate_pct": round(win_rate, 2),
        "net_pnl": round(sum(pnls), 2),
        "gross_profit": round(sum(wins), 2),
        "gross_loss": round(sum(losses), 2),
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses else 999.0,
        "sharpe_ratio": round(_sharpe(returns), 2),
        "sortino_ratio": round(_sortino(returns), 2),
        "max_drawdown_pct": _max_drawdown(equity),
        "equity_curve": equity[-100:],
        "avg_win": round(np.mean(wins), 2) if wins else 0,
        "avg_loss": round(np.mean(losses), 2) if losses else 0,
        "account": account,
        "ai_analytics": ai_service.analytics,
        "risk": order_manager.risk_engine.status_dict(),
    }


@router.get("/equity-curve")
async def equity_curve(limit: int = Query(100, le=500)):
    summary = await performance_summary()
    return {"equity_curve": summary["equity_curve"], "net_pnl": summary["net_pnl"]}


@router.get("/ai-quality")
async def ai_quality():
    hist = ai_service.signal_history[-100:]
    if not hist:
        return {"status": "no_data"}
    confidences = [s.get("confidence_score", 0) for s in hist]
    actions = [s.get("action") for s in hist]
    return {
        "samples": len(hist),
        "avg_confidence": round(float(np.mean(confidences)), 2),
        "buy_pct": round(actions.count("BUY") / len(actions) * 100, 1),
        "sell_pct": round(actions.count("SELL") / len(actions) * 100, 1),
        "hold_pct": round(actions.count("HOLD") / len(actions) * 100, 1),
    }
