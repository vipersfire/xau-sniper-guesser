from datetime import datetime
from sqlalchemy import Index, String, Float, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class OHLCVBar(Base):
    __tablename__ = "ohlcv_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    spread: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    __table_args__ = (
        Index("ix_ohlcv_symbol_tf_ts", "symbol", "timeframe", "timestamp", unique=True),
        Index("ix_ohlcv_ts", "timestamp"),
    )
