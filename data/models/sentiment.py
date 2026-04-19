from datetime import datetime
from sqlalchemy import Index, String, Float, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class SentimentSnapshot(Base):
    __tablename__ = "sentiment_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    long_pct: Mapped[float] = mapped_column(Float, nullable=False)
    short_pct: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="oanda")

    __table_args__ = (
        Index("ix_sentiment_symbol_ts", "symbol", "timestamp", unique=True),
    )
