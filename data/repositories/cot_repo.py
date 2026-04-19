from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from data.models.cot import COTReport


class COTRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, data: dict):
        stmt = insert(COTReport).values(**data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["report_date", "market_name"],
            set_={k: stmt.excluded.__getattr__(k) for k in data if k not in ("report_date", "market_name")},
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def latest(self, market_name: str) -> COTReport | None:
        q = (
            select(COTReport)
            .where(COTReport.market_name == market_name)
            .order_by(COTReport.report_date.desc())
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def latest_date(self, market_name: str) -> date | None:
        q = select(func.max(COTReport.report_date)).where(COTReport.market_name == market_name)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def get_range(self, market_name: str, start: date, end: date | None = None) -> list[COTReport]:
        q = select(COTReport).where(
            COTReport.market_name == market_name,
            COTReport.report_date >= start,
        )
        if end:
            q = q.where(COTReport.report_date <= end)
        q = q.order_by(COTReport.report_date)
        result = await self.session.execute(q)
        return list(result.scalars().all())
