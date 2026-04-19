from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from data.models.trade import Trade


class TradeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, trade: Trade) -> Trade:
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade

    async def update(self, trade: Trade) -> Trade:
        await self.session.merge(trade)
        await self.session.commit()
        return trade

    async def get(self, trade_id: int) -> Trade | None:
        return await self.session.get(Trade, trade_id)

    async def get_open(self) -> list[Trade]:
        q = select(Trade).where(Trade.status == "open").order_by(Trade.open_time)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_ticket(self, ticket: int) -> Trade | None:
        q = select(Trade).where(Trade.ticket == ticket).limit(1)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def total_pnl_today(self) -> float:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        q = select(func.sum(Trade.pnl)).where(
            Trade.close_time >= start,
            Trade.status == "closed",
        )
        result = await self.session.execute(q)
        return float(result.scalar_one() or 0.0)

    async def account_drawdown_24h(self) -> float:
        """Sum of losses in last 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        q = select(func.sum(Trade.pnl)).where(
            Trade.close_time >= cutoff,
            Trade.status == "closed",
            Trade.pnl < 0,
        )
        result = await self.session.execute(q)
        return abs(float(result.scalar_one() or 0.0))

    async def win_rate_by_regime(self) -> dict[str, float]:
        q = select(Trade.regime_type, func.count(Trade.id), func.sum(Trade.pnl)).where(
            Trade.status == "closed", Trade.regime_type.isnot(None)
        ).group_by(Trade.regime_type)
        result = await self.session.execute(q)
        rows = result.all()
        stats = {}
        for regime, count, total_pnl in rows:
            stats[regime] = {"count": count, "total_pnl": float(total_pnl or 0)}
        return stats
