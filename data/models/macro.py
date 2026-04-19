from datetime import date
from sqlalchemy import Index, String, Float, Date, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class MacroDataPoint(Base):
    """FRED macro indicator. Realtime vs revised stored separately."""
    __tablename__ = "macro_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. DGS10, DFII10
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=True)
    is_realtime: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    realtime_start: Mapped[date] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_macro_series_date_rt", "series_id", "observation_date", "is_realtime", unique=True),
    )
