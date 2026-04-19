"""Detector C: Calendar hard flag for unknown/high-impact events."""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class CalendarDetector:
    """Hard flag based on ForexFactory economic calendar."""

    def __init__(self, window_minutes: int = 30, impact_levels: list[str] | None = None):
        self._window_minutes = window_minutes
        self._impact_levels = impact_levels or ["High"]

    async def is_anomaly(self, dt: datetime | None = None) -> bool:
        dt = dt or datetime.now(timezone.utc)
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.event_repo import EventRepository
            async with AsyncSessionLocal() as session:
                repo = EventRepository(session)
                return await repo.has_high_impact_in_window(dt, self._window_minutes)
        except Exception as e:
            logger.warning("Calendar detector failed: %s — defaulting to not anomalous", e)
            return False

    async def score(self, dt: datetime | None = None) -> float:
        """Binary: 1.0 if high-impact event near, else 0.0."""
        return 1.0 if await self.is_anomaly(dt) else 0.0
