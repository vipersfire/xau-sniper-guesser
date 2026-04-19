"""Reuters gold RSS importer — rule-based, no AI."""
import aiohttp
import logging
from ingestion.base.importer import BaseImporter
from ingestion.parsers.rss_parser import parse_rss

logger = logging.getLogger(__name__)

REUTERS_RSS_URL = "https://feeds.reuters.com/reuters/businessNews"


class ReutersRSSImporter(BaseImporter):
    source_name = "reuters_rss"
    run_interval = 3600  # hourly

    async def fetch(self) -> str:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; XAUSniper/1.0)"}
        async with aiohttp.ClientSession(headers=headers) as http:
            async with http.get(REUTERS_RSS_URL) as resp:
                resp.raise_for_status()
                return await resp.text()

    async def parse(self, raw: str) -> list[dict]:
        items = parse_rss(raw)
        gold_keywords = {"gold", "xau", "bullion", "precious metal", "fed", "rate", "dollar", "dxy"}
        filtered = []
        for item in items:
            text = (item.title + " " + item.summary).lower()
            if any(kw in text for kw in gold_keywords):
                filtered.append({
                    "title": item.title,
                    "link": item.link,
                    "published": item.published,
                    "summary": item.summary[:500],
                    "source": "reuters",
                })
        return filtered

    async def store(self, data: list[dict]) -> int:
        for item in data:
            logger.debug("Reuters: [%s] %s", item.get("published"), item.get("title"))
        return len(data)
