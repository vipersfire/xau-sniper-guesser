"""Sentiment signals: COT ratio, retail bias. No AI — all numbers."""
import logging
from config.constants import SYMBOL

logger = logging.getLogger(__name__)


class SentimentSignals:
    async def extract_features(self) -> dict:
        features = {}
        try:
            features["retail_long_pct"] = await self._retail_long_pct()
            features["cot_net_noncomm_norm"] = await self._cot_net_norm()
            features["news_pressure_score"] = await self._news_pressure()
        except Exception as e:
            logger.warning("Sentiment features unavailable: %s", e)
            features = {"retail_long_pct": 50.0, "cot_net_noncomm_norm": 0.0, "news_pressure_score": 0}
        return features

    async def _retail_long_pct(self) -> float:
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.sentiment_repo import SentimentRepository
            async with AsyncSessionLocal() as session:
                repo = SentimentRepository(session)
                snap = await repo.latest(SYMBOL)
            if snap:
                return float(snap.long_pct)
        except Exception:
            pass
        return 50.0

    async def _cot_net_norm(self) -> float:
        """Normalize COT net non-commercial position to [-1, 1]."""
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.cot_repo import COTRepository
            import numpy as np
            from datetime import date, timedelta
            async with AsyncSessionLocal() as session:
                repo = COTRepository(session)
                reports = await repo.get_range("GOLD_COT", date.today() - timedelta(days=365))
            if not reports:
                return 0.0
            nets = [r.net_noncomm for r in reports]
            latest = nets[-1]
            max_abs = max(abs(n) for n in nets)
            return round(float(latest / max_abs), 4) if max_abs > 0 else 0.0
        except Exception:
            return 0.0

    async def _news_pressure(self) -> int:
        """Count of High-impact events in next 24h."""
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.event_repo import EventRepository
            async with AsyncSessionLocal() as session:
                repo = EventRepository(session)
                return await repo.count_high_impact_next_24h()
        except Exception:
            return 0
