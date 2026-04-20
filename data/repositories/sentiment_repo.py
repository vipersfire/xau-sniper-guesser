from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.sentiment import DerivedSentimentSnapshot


class SentimentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        symbol: str,
        timestamp: datetime,
        range_position: float = 0.5,
        retail_trap_score: float = 0.0,
        cot_divergence: float = 0.0,
        session_momentum: float = 0.0,
        composite_score: float = 0.0,
        source: str = "derived",
        meta: dict | None = None,
    ) -> None:
        values = dict(
            symbol=symbol,
            timestamp=timestamp,
            range_position=range_position,
            retail_trap_score=retail_trap_score,
            cot_divergence=cot_divergence,
            session_momentum=session_momentum,
            composite_score=composite_score,
            source=source,
            meta=meta or {},
        )
        stmt = insert(DerivedSentimentSnapshot).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timestamp"],
            set_={k: stmt.excluded[k] for k in values if k not in ("symbol", "timestamp")},
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def latest(self, symbol: str) -> DerivedSentimentSnapshot | None:
        q = (
            select(DerivedSentimentSnapshot)
            .where(DerivedSentimentSnapshot.symbol == symbol)
            .order_by(DerivedSentimentSnapshot.timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def latest_timestamp(self, symbol: str) -> datetime | None:
        q = select(func.max(DerivedSentimentSnapshot.timestamp)).where(
            DerivedSentimentSnapshot.symbol == symbol
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def get_range(self, symbol: str, since: datetime) -> list[DerivedSentimentSnapshot]:
        q = (
            select(DerivedSentimentSnapshot)
            .where(
                DerivedSentimentSnapshot.symbol == symbol,
                DerivedSentimentSnapshot.timestamp >= since,
            )
            .order_by(DerivedSentimentSnapshot.timestamp.asc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
