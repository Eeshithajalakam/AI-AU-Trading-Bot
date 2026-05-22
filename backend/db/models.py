"""SQLAlchemy ORM models for persistent storage."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True)
    asset: Mapped[str] = mapped_column(String(32), default="XAU/USD")
    action: Mapped[str] = mapped_column(String(16))
    trend: Mapped[str] = mapped_column(String(16))
    current_price: Mapped[float] = mapped_column(Float)
    predicted_price: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str | None] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), default="XAUUSD")
    action: Mapped[str] = mapped_column(String(16))
    volume: Mapped[float] = mapped_column(Float, default=0.01)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    paper_trade: Mapped[bool] = mapped_column(Boolean, default=False)
    mt5_ticket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    days: Mapped[int] = mapped_column(Integer)
    initial_capital: Mapped[float] = mapped_column(Float)
    final_capital: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    win_rate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_signals: Mapped[int] = mapped_column(Integer, default=0)
    bullish_signals: Mapped[int] = mapped_column(Integer, default=0)
    bearish_signals: Mapped[int] = mapped_column(Integer, default=0)
    neutral_signals: Mapped[int] = mapped_column(Integer, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    daily_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    open_positions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    epochs: Mapped[int] = mapped_column(Integer, default=25)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    current_epoch: Mapped[int] = mapped_column(Integer, default=0)
    train_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    directional_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
