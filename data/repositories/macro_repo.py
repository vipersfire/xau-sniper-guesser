from datetime import date
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.macro import MacroDataPoint


class MacroRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, series_id: str, observation_date: date, value: float, is_realtime: bool = True, realtime_start: date | None = None):
        stmt = insert(MacroDataPoint).values(
            series_id=series_id,
            observation_date=observation_date,
            value=value,
            is_realtime=is_realtime,
            realtime_start=realtime_start,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["series_id", "observation_date", "is_realtime"],
            set_={"value": stmt.excluded.value},
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_series(
        self,
        series_id: str,
        start: date,
        end: date | None = None,
        is_realtime: bool = True,
    ) -> list[MacroDataPoint]:
        q = select(MacroDataPoint).where(
            and_(
                MacroDataPoint.series_id == series_id,
                MacroDataPoint.observation_date >= start,
                MacroDataPoint.is_realtime == is_realtime,
            )
        )
        if end:
            q = q.where(MacroDataPoint.observation_date <= end)
        q = q.order_by(MacroDataPoint.observation_date)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def latest_value(self, series_id: str, is_realtime: bool = True) -> float | None:
        q = (
            select(MacroDataPoint.value)
            .where(
                MacroDataPoint.series_id == series_id,
                MacroDataPoint.is_realtime == is_realtime,
                MacroDataPoint.value.isnot(None),
            )
            .order_by(MacroDataPoint.observation_date.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def latest_date(self, series_id: str, is_realtime: bool = True) -> date | None:
        q = (
            select(func.max(MacroDataPoint.observation_date))
            .where(MacroDataPoint.series_id == series_id, MacroDataPoint.is_realtime == is_realtime)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()
