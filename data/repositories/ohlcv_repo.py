from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.ohlcv import OHLCVBar


class OHLCVRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_bars(self, bars: list[dict]):
        if not bars:
            return
        stmt = insert(OHLCVBar).values(bars)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "spread": stmt.excluded.spread,
                "quality_score": stmt.excluded.quality_score,
                "flags": stmt.excluded.flags,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        min_quality: float = 0.0,
    ) -> list[OHLCVBar]:
        q = select(OHLCVBar).where(
            and_(
                OHLCVBar.symbol == symbol,
                OHLCVBar.timeframe == timeframe,
                OHLCVBar.timestamp >= start,
                OHLCVBar.quality_score >= min_quality,
            )
        )
        if end:
            q = q.where(OHLCVBar.timestamp <= end)
        q = q.order_by(OHLCVBar.timestamp)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count(self, symbol: str | None = None, timeframe: str | None = None) -> int:
        q = select(func.count(OHLCVBar.id))
        if symbol:
            q = q.where(OHLCVBar.symbol == symbol)
        if timeframe:
            q = q.where(OHLCVBar.timeframe == timeframe)
        result = await self.session.execute(q)
        return result.scalar_one()

    async def latest_timestamp(self, symbol: str, timeframe: str) -> datetime | None:
        q = select(func.max(OHLCVBar.timestamp)).where(
            OHLCVBar.symbol == symbol, OHLCVBar.timeframe == timeframe
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def avg_spread(self, symbol: str, timeframe: str, session_name: str | None = None) -> float:
        q = select(func.avg(OHLCVBar.spread)).where(
            OHLCVBar.symbol == symbol,
            OHLCVBar.timeframe == timeframe,
            OHLCVBar.spread > 0,
        )
        result = await self.session.execute(q)
        return float(result.scalar_one() or 0.0)
