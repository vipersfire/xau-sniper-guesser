import aiohttp
import logging
from datetime import datetime, timezone
from ingestion.base.importer import BaseImporter
from data.db import AsyncSessionLocal
from data.repositories.sentiment_repo import SentimentRepository
from config.settings import settings
from config.constants import SYMBOL
from utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)

# OANDA open position ratio endpoint
OANDA_BASE = {
    "practice": "https://api-fxpractice.oanda.com",
    "live": "https://api-fxtrade.oanda.com",
}


class OANDASentimentImporter(BaseImporter):
    source_name = "oanda_sentiment"
    run_interval = 900  # 15 minutes

    async def fetch(self) -> dict:
        base = OANDA_BASE.get(settings.oanda_environment, OANDA_BASE["practice"])
        url = f"{base}/v3/instruments/XAU_USD/positionBook"
        headers = {"Authorization": f"Bearer {settings.oanda_api_key}"}
        async with aiohttp.ClientSession(headers=headers) as http:
            return await async_retry_with_backoff(
                self._fetch_book, http, url, max_attempts=4, base_delay=2.0
            )

    async def _fetch_book(self, http: aiohttp.ClientSession, url: str) -> dict:
        async with http.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def parse(self, raw: dict) -> dict | None:
        book = raw.get("positionBook", {})
        buckets = book.get("buckets", [])
        if not buckets:
            return None
        long_count = sum(float(b.get("longCountPercent", 0)) for b in buckets)
        short_count = sum(float(b.get("shortCountPercent", 0)) for b in buckets)
        total = long_count + short_count
        if total == 0:
            return None
        return {
            "symbol": SYMBOL,
            "timestamp": datetime.now(timezone.utc),
            "long_pct": round(long_count / total * 100, 2),
            "short_pct": round(short_count / total * 100, 2),
            "source": "oanda",
        }

    async def store(self, data: dict | None) -> int:
        if not data:
            return 0
        async with AsyncSessionLocal() as session:
            repo = SentimentRepository(session)
            await repo.upsert(**data)
        return 1
