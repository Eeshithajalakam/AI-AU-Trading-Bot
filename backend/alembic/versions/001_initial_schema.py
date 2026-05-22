"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(64), nullable=True),
        sa.Column("asset", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("trend", sa.String(16), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("predicted_price", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_external_id", "signals", ["external_id"])

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("signal_id", sa.String(64), nullable=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=True),
        sa.Column("sl", sa.Float(), nullable=True),
        sa.Column("tp", sa.Float(), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("paper_trade", sa.Boolean(), nullable=False),
        sa.Column("mt5_ticket", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_signal_id", "trades", ["signal_id"])
    op.create_index("ix_trades_status", "trades", ["status"])

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("final_capital", sa.Float(), nullable=True),
        sa.Column("net_profit", sa.Float(), nullable=True),
        sa.Column("roi_pct", sa.Float(), nullable=True),
        sa.Column("win_rate_pct", sa.Float(), nullable=True),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=True),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"], unique=True)

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("total_signals", sa.Integer(), nullable=False),
        sa.Column("bullish_signals", sa.Integer(), nullable=False),
        sa.Column("bearish_signals", sa.Integer(), nullable=False),
        sa.Column("neutral_signals", sa.Integer(), nullable=False),
        sa.Column("average_confidence", sa.Float(), nullable=False),
        sa.Column("daily_pnl", sa.Float(), nullable=False),
        sa.Column("open_positions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "training_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("epochs", sa.Integer(), nullable=False),
        sa.Column("progress_pct", sa.Float(), nullable=False),
        sa.Column("current_epoch", sa.Integer(), nullable=False),
        sa.Column("train_loss", sa.Float(), nullable=True),
        sa.Column("val_mae", sa.Float(), nullable=True),
        sa.Column("val_rmse", sa.Float(), nullable=True),
        sa.Column("directional_accuracy", sa.Float(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("training_jobs")
    op.drop_table("analytics_snapshots")
    op.drop_table("app_settings")
    op.drop_table("backtest_runs")
    op.drop_table("trades")
    op.drop_table("signals")
