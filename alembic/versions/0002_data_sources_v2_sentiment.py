"""Data Sources v2 — replace OANDA sentiment columns with derived sentiment

Drops the OANDA-sourced long_pct / short_pct columns from sentiment_snapshots
and adds the derived sentiment fields: range_position, retail_trap_score,
cot_divergence, session_momentum, composite_score, and meta (JSON).

Existing rows have their source updated to "derived" and receive neutral
default values so no data is lost (rows simply mark the transition point).

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add new derived sentiment columns ────────────────────────────────────
    op.add_column("sentiment_snapshots", sa.Column(
        "range_position", sa.Float(), nullable=False, server_default="0.5",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "retail_trap_score", sa.Float(), nullable=False, server_default="0.0",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "cot_divergence", sa.Float(), nullable=False, server_default="0.0",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "session_momentum", sa.Float(), nullable=False, server_default="0.0",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "composite_score", sa.Float(), nullable=False, server_default="0.0",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "meta", postgresql.JSON(), nullable=False, server_default="{}",
    ))

    # ── Migrate existing rows — mark them as legacy OANDA data ───────────────
    # Compute a rough composite from long_pct so history isn't lost.
    # composite = (long_pct/100 - 0.5) * 2  → maps 0–100 to [-1, +1]
    op.execute("""
        UPDATE sentiment_snapshots
        SET
            range_position   = LEAST(GREATEST(long_pct / 100.0, 0.0), 1.0),
            composite_score  = LEAST(GREATEST((long_pct / 100.0 - 0.5) * 2.0, -1.0), 1.0),
            source           = 'oanda_legacy',
            meta             = jsonb_build_object(
                                   'migrated_from', 'oanda',
                                   'original_long_pct',  long_pct,
                                   'original_short_pct', short_pct
                               )
        WHERE source = 'oanda'
    """)

    # ── Drop old OANDA-specific columns ─────────────────────────────────────
    op.drop_column("sentiment_snapshots", "long_pct")
    op.drop_column("sentiment_snapshots", "short_pct")

    # ── Update default source value for future rows ──────────────────────────
    op.alter_column(
        "sentiment_snapshots",
        "source",
        existing_type=sa.String(50),
        server_default="derived",
    )


def downgrade() -> None:
    # Restore OANDA columns, recover data from meta JSON where available
    op.add_column("sentiment_snapshots", sa.Column(
        "long_pct", sa.Float(), nullable=False, server_default="50.0",
    ))
    op.add_column("sentiment_snapshots", sa.Column(
        "short_pct", sa.Float(), nullable=False, server_default="50.0",
    ))

    op.execute("""
        UPDATE sentiment_snapshots
        SET
            long_pct  = COALESCE((meta->>'original_long_pct')::float,  50.0),
            short_pct = COALESCE((meta->>'original_short_pct')::float, 50.0),
            source    = 'oanda'
        WHERE source = 'oanda_legacy'
    """)

    op.drop_column("sentiment_snapshots", "meta")
    op.drop_column("sentiment_snapshots", "composite_score")
    op.drop_column("sentiment_snapshots", "session_momentum")
    op.drop_column("sentiment_snapshots", "cot_divergence")
    op.drop_column("sentiment_snapshots", "retail_trap_score")
    op.drop_column("sentiment_snapshots", "range_position")

    op.alter_column(
        "sentiment_snapshots",
        "source",
        existing_type=sa.String(50),
        server_default="oanda",
    )
