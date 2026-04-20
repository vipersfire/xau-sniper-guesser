"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ohlcv_bars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("flags", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ohlcv_symbol_tf_ts", "ohlcv_bars", ["symbol", "timeframe", "timestamp"], unique=True)

    op.create_table(
        "macro_data_points",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("series_id", sa.String(50), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("is_realtime", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("realtime_start", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_macro_series_date", "macro_data_points", ["series_id", "observation_date"], unique=True)

    op.create_table(
        "sentiment_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("long_pct", sa.Float(), nullable=False),
        sa.Column("short_pct", sa.Float(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="oanda"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sentiment_symbol_ts", "sentiment_snapshots", ["symbol", "timestamp"], unique=True)

    op.create_table(
        "cot_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("market_name", sa.String(100), nullable=False),
        sa.Column("comm_long", sa.Integer(), nullable=False),
        sa.Column("comm_short", sa.Integer(), nullable=False),
        sa.Column("noncomm_long", sa.Integer(), nullable=False),
        sa.Column("noncomm_short", sa.Integer(), nullable=False),
        sa.Column("net_noncomm", sa.Integer(), nullable=False),
        sa.Column("net_noncomm_delta_wow", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_interest", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cot_market_date", "cot_reports", ["market_name", "report_date"], unique=True)

    op.create_table(
        "economic_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("event_name", sa.String(200), nullable=False),
        sa.Column("impact", sa.String(20), nullable=False, server_default="Low"),
        sa.Column("forecast", sa.String(50), nullable=True),
        sa.Column("actual", sa.String(50), nullable=True),
        sa.Column("previous", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_time", "economic_events", ["event_time"])
    op.create_index("ix_events_currency_time", "economic_events", ["currency", "event_time"])

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket", sa.BigInteger(), nullable=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("sl_price", sa.Float(), nullable=False),
        sa.Column("tp_price", sa.Float(), nullable=False),
        sa.Column("lot_size", sa.Float(), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("r_multiple", sa.Float(), nullable=True),
        sa.Column("regime_type", sa.String(50), nullable=True),
        sa.Column("anomaly_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("meta", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_open_time", "trades", ["open_time"])
    op.create_index("ix_trades_status", "trades", ["status"])


def downgrade() -> None:
    op.drop_table("trades")
    op.drop_table("economic_events")
    op.drop_table("cot_reports")
    op.drop_table("sentiment_snapshots")
    op.drop_table("macro_data_points")
    op.drop_table("ohlcv_bars")
