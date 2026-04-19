from datetime import date
from sqlalchemy import Index, String, Float, Date, Integer, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from data.db import Base


class COTReport(Base):
    __tablename__ = "cot_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    market_name: Mapped[str] = mapped_column(String(100), nullable=False)
    comm_long: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    comm_short: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    noncomm_long: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    noncomm_short: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    net_noncomm: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    net_noncomm_delta_wow: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    open_interest: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_cot_date_market", "report_date", "market_name", unique=True),
    )
