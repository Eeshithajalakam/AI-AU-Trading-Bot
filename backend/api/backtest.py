from fastapi import APIRouter, Query
from trading.backtester import BacktestEngine
from core.database import AsyncSessionLocal
from db.repository import BacktestRepository

router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


@router.post("/run")
async def run_backtest(
    days: int = Query(30),
    capital: float = Query(10000.0),
):
    engine = BacktestEngine(initial_capital=capital)
    df = await engine.load_historical_data(days=days)
    report = await engine.run_backtest(df)

    if "error" not in report:
        try:
            async with AsyncSessionLocal() as session:
                row = await BacktestRepository.create(session, days, capital, report)
                report["run_id"] = row.id
        except Exception:
            pass

    return report


@router.get("/history")
async def backtest_history(limit: int = Query(10, le=50)):
    try:
        async with AsyncSessionLocal() as session:
            runs = await BacktestRepository.list_recent(session, limit)
            return [
                {
                    "id": r.id,
                    "days": r.days,
                    "roi_pct": r.roi_pct,
                    "win_rate_pct": r.win_rate_pct,
                    "sharpe_ratio": r.sharpe_ratio,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in runs
            ]
    except Exception:
        return []
