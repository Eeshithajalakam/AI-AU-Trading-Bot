"""Data access layer for PostgreSQL persistence."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Signal, Trade, BacktestRun, AppSettings, AnalyticsSnapshot, TrainingJob


class SignalRepository:
    @staticmethod
    async def create(session: AsyncSession, data: dict[str, Any]) -> Signal:
        row = Signal(
            external_id=data.get("id") or data.get("external_id"),
            asset=data.get("asset", "XAU/USD"),
            action=data.get("action", "HOLD"),
            trend=data.get("trend", "NEUTRAL"),
            current_price=float(data.get("current_price", 0)),
            predicted_price=float(data.get("predicted_price", 0)),
            confidence_score=float(data.get("confidence_score", 0)),
            metrics=data.get("metrics"),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_recent(session: AsyncSession, limit: int = 50) -> list[Signal]:
        result = await session.execute(
            select(Signal).order_by(desc(Signal.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest(session: AsyncSession) -> Signal | None:
        result = await session.execute(
            select(Signal).order_by(desc(Signal.created_at)).limit(1)
        )
        return result.scalar_one_or_none()


class TradeRepository:
    @staticmethod
    async def create(session: AsyncSession, data: dict[str, Any]) -> Trade:
        row = Trade(
            signal_id=data.get("signal_id"),
            symbol=data.get("symbol", "XAUUSD"),
            action=data.get("action", "HOLD"),
            volume=float(data.get("volume", 0.01)),
            entry_price=data.get("entry_price"),
            sl=data.get("sl"),
            tp=data.get("tp"),
            exit_price=data.get("exit_price"),
            pnl=data.get("pnl"),
            status=data.get("status", "PENDING"),
            paper_trade=bool(data.get("paper_trade", False)),
            mt5_ticket=data.get("mt5_ticket"),
            details=data.get("details"),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_recent(session: AsyncSession, limit: int = 50) -> list[Trade]:
        result = await session.execute(
            select(Trade).order_by(desc(Trade.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def daily_pnl(session: AsyncSession) -> float:
        today = datetime.now(timezone.utc).date()
        result = await session.execute(
            select(func.coalesce(func.sum(Trade.pnl), 0.0)).where(
                func.date(Trade.created_at) == today,
                Trade.status == "EXECUTED",
            )
        )
        return float(result.scalar() or 0.0)

    @staticmethod
    async def open_trade_count(session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count()).select_from(Trade).where(Trade.status == "OPEN")
        )
        return int(result.scalar() or 0)


class BacktestRepository:
    @staticmethod
    async def create(session: AsyncSession, days: int, capital: float, report: dict) -> BacktestRun:
        summary = report.get("summary", {})
        metrics = report.get("metrics", {})
        row = BacktestRun(
            days=days,
            initial_capital=capital,
            final_capital=summary.get("final_capital"),
            net_profit=summary.get("net_profit"),
            roi_pct=summary.get("roi_pct"),
            win_rate_pct=summary.get("win_rate_pct"),
            sharpe_ratio=metrics.get("sharpe_ratio"),
            max_drawdown_pct=metrics.get("max_drawdown_pct"),
            total_trades=summary.get("total_trades"),
            report=report,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def list_recent(session: AsyncSession, limit: int = 20) -> list[BacktestRun]:
        result = await session.execute(
            select(BacktestRun).order_by(desc(BacktestRun.created_at)).limit(limit)
        )
        return list(result.scalars().all())


class SettingsRepository:
    @staticmethod
    async def get(session: AsyncSession, key: str, default: dict | None = None) -> dict:
        result = await session.execute(select(AppSettings).where(AppSettings.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else (default or {})

    @staticmethod
    async def upsert(session: AsyncSession, key: str, value: dict) -> AppSettings:
        result = await session.execute(select(AppSettings).where(AppSettings.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            row = AppSettings(key=key, value=value)
            session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


class AnalyticsRepository:
    @staticmethod
    async def save_snapshot(session: AsyncSession, data: dict[str, Any]) -> AnalyticsSnapshot:
        row = AnalyticsSnapshot(
            total_signals=data.get("total_signals", 0),
            bullish_signals=data.get("bullish_signals", 0),
            bearish_signals=data.get("bearish_signals", 0),
            neutral_signals=data.get("neutral_signals", 0),
            average_confidence=data.get("average_confidence", 0.0),
            daily_pnl=data.get("daily_pnl", 0.0),
            open_positions=data.get("open_positions", 0),
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def get_latest(session: AsyncSession) -> AnalyticsSnapshot | None:
        result = await session.execute(
            select(AnalyticsSnapshot).order_by(desc(AnalyticsSnapshot.created_at)).limit(1)
        )
        return result.scalar_one_or_none()


class TrainingRepository:
    @staticmethod
    async def create_job(session: AsyncSession, epochs: int) -> TrainingJob:
        row = TrainingJob(status="running", epochs=epochs, message="Training started")
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def update_job(session: AsyncSession, job_id: int, **kwargs: Any) -> TrainingJob | None:
        result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        for k, v in kwargs.items():
            setattr(row, k, v)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def get_latest(session: AsyncSession) -> TrainingJob | None:
        result = await session.execute(
            select(TrainingJob).order_by(desc(TrainingJob.created_at)).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, job_id: int) -> TrainingJob | None:
        result = await session.execute(select(TrainingJob).where(TrainingJob.id == job_id))
        return result.scalar_one_or_none()
