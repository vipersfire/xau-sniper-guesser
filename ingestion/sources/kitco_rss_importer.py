"""Kitco RSS news importer — rule-based, no AI."""
import aiohttp
import logging
from ingestion.base.importer import BaseImporter
from ingestion.parsers.rss_parser import parse_rss

logger = logging.getLogger(__name__)

KITCO_RSS_URL = "https://www.kitco.com/rss/news/kitco-metals-news.xml"


class KitcoRSSImporter(BaseImporter):
    source_name = "kitco_rss"
    run_interval = 3600  # hourly

    async def fetch(self) -> str:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; XAUSniper/1.0)"}
        async with aiohttp.ClientSession(headers=headers) as http:
            async with http.get(KITCO_RSS_URL) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def parse(self, raw: str) -> list[dict]:
        items = parse_rss(raw)
        return [
            {
                "title": item.title,
                "link": item.link,
                "published": item.published,
                "summary": item.summary[:500] if item.summary else "",
                "source": "kitco",
            }
            for item in items
        ]

    async def store(self, data: list[dict]) -> int:
        # News headlines are used for anomaly scoring only — logged, not persisted
        for item in data:
            logger.debug("Kitco: [%s] %s", item.get("published"), item.get("title"))
        return len(data)
