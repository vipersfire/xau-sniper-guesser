import aiohttp
import logging
from datetime import date, timedelta
from ingestion.base.importer import BaseImporter
from ingestion.parsers.csv_parser import parse_fred_csv
from data.db import AsyncSessionLocal
from data.repositories.macro_repo import MacroRepository
from config.settings import settings
from utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)

FRED_SERIES = {
    "DGS10":   "10-Year Treasury Constant Maturity Rate",
    "DFII10":  "10-Year TIPS Real Yield",
    "DFF":     "Fed Funds Effective Rate",
    "CPIAUCSL": "CPI All Urban Consumers",
    "T10YIE":  "10-Year Breakeven Inflation",
}

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


class FREDImporter(BaseImporter):
    source_name = "fred"
    run_interval = 86400  # daily

    async def fetch(self) -> dict[str, str]:
        results = {}
        headers = {"User-Agent": "xau-sniper-guesser/1.0 (research; send.faisalhazmi@gmail.com)"}
        async with aiohttp.ClientSession(headers=headers) as http:
            for series_id in FRED_SERIES:
                results[series_id] = await async_retry_with_backoff(
                    self._fetch_series, http, series_id,
                    max_attempts=4, base_delay=2.0,
                )
        return results

    async def _fetch_series(self, http: aiohttp.ClientSession, series_id: str) -> str:
        params = {
            "series_id": series_id,
            "api_key": settings.fred_api_key,
            "file_type": "json",
            "observation_start": (date.today() - timedelta(days=3650)).isoformat(),
        }
        async with http.get(FRED_BASE, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def parse(self, raw: dict) -> list[dict]:
        records = []
        for series_id, data in raw.items():
            if isinstance(data, dict) and "observations" in data:
                for obs in data["observations"]:
                    val_str = obs.get("value", ".")
                    if val_str == ".":
                        continue
                    try:
                        records.append({
                            "series_id": series_id,
                            "observation_date": date.fromisoformat(obs["date"]),
                            "value": float(val_str),
                            "is_realtime": True,
                            "realtime_start": date.fromisoformat(obs.get("realtime_start", obs["date"])),
                        })
                    except (ValueError, KeyError):
                        continue
        return records

    async def store(self, data: list[dict]) -> int:
        async with AsyncSessionLocal() as session:
            repo = MacroRepository(session)
            for rec in data:
                await repo.upsert(**rec)
        return len(data)
