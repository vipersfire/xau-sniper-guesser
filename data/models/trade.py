from datetime import datetime
from sqlalchemy import Index, String, Float, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket: Mapped[int | None] = mapped_column(Integer, nullable=True)  # MT5 ticket
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)   # buy | sell
    regime_type: Mapped[str] = mapped_column(String(50), nullable=True)
    regime_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    entry_price: Mapped[float] = mapped_column(Float, nullable=True)
    sl_price: Mapped[float] = mapped_column(Float, nullable=True)
    tp_price: Mapped[float] = mapped_column(Float, nullable=True)
    lot_size: Mapped[float] = mapped_column(Float, nullable=False)
    open_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    r_multiple: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_trade_status", "status"),
        Index("ix_trade_open_time", "open_time"),
    )
