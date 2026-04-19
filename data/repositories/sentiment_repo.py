from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.sentiment import SentimentSnapshot


class SentimentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, symbol: str, timestamp: datetime, long_pct: float, short_pct: float, source: str = "oanda"):
        stmt = insert(SentimentSnapshot).values(
            symbol=symbol, timestamp=timestamp, long_pct=long_pct, short_pct=short_pct, source=source
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timestamp"],
            set_={"long_pct": stmt.excluded.long_pct, "short_pct": stmt.excluded.short_pct},
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def latest(self, symbol: str) -> SentimentSnapshot | None:
        q = (
            select(SentimentSnapshot)
            .where(SentimentSnapshot.symbol == symbol)
            .order_by(SentimentSnapshot.timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def latest_timestamp(self, symbol: str) -> datetime | None:
        q = select(func.max(SentimentSnapshot.timestamp)).where(SentimentSnapshot.symbol == symbol)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()
