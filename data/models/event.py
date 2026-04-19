from datetime import datetime
from sqlalchemy import Index, String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class EconomicEvent(Base):
    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    impact: Mapped[str] = mapped_column(String(20), nullable=False)  # Low, Medium, High
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    forecast: Mapped[str | None] = mapped_column(String(50), nullable=True)
    previous: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actual: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="forexfactory")

    __table_args__ = (
        Index("ix_event_time_currency", "event_time", "currency"),
        Index("ix_event_time", "event_time"),
    )
