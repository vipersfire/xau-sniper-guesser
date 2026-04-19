from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.event import EconomicEvent


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_events(self, events: list[dict]):
        if not events:
            return
        for ev in events:
            stmt = insert(EconomicEvent).values(**ev)
            stmt = stmt.on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.commit()

    async def get_upcoming(self, hours_ahead: int = 24, impact: str | None = None) -> list[EconomicEvent]:
        now = datetime.utcnow()
        q = select(EconomicEvent).where(
            EconomicEvent.event_time >= now,
            EconomicEvent.event_time <= now + timedelta(hours=hours_ahead),
        )
        if impact:
            q = q.where(EconomicEvent.impact == impact)
        q = q.order_by(EconomicEvent.event_time)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def has_high_impact_in_window(self, dt: datetime, window_minutes: int = 30) -> bool:
        half = timedelta(minutes=window_minutes / 2)
        q = select(EconomicEvent).where(
            and_(
                EconomicEvent.event_time >= dt - half,
                EconomicEvent.event_time <= dt + half,
                EconomicEvent.impact == "High",
            )
        ).limit(1)
        result = await self.session.execute(q)
        return result.scalar_one_or_none() is not None

    async def count_high_impact_next_24h(self) -> int:
        from sqlalchemy import func
        now = datetime.utcnow()
        q = select(func.count(EconomicEvent.id)).where(
            EconomicEvent.event_time >= now,
            EconomicEvent.event_time <= now + timedelta(hours=24),
            EconomicEvent.impact == "High",
        )
        result = await self.session.execute(q)
        return result.scalar_one()
