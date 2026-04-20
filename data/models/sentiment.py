from datetime import datetime
from sqlalchemy import Index, String, Float, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class DerivedSentimentSnapshot(Base):
    """Sentiment derived entirely from price structure + COT — no external API."""
    __tablename__ = "sentiment_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Range position: where price sits within recent high-low range [0=bottom, 1=top]
    range_position: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    # Retail trap score [0=no trap, 1=strong trap signal]
    retail_trap_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # COT divergence: how much non-comm positioning diverges from price action [-1, 1]
    cot_divergence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Session momentum: directional bias based on session open vs current price [-1, 1]
    session_momentum: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Composite sentiment score [-1 bearish, +1 bullish]
    composite_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="derived")

    # Optional metadata (e.g. lookback bars used, component values)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_sentiment_symbol_ts", "symbol", "timestamp", unique=True),
    )
