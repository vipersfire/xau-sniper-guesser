import aiohttp
import logging
from datetime import date
from ingestion.base.importer import BaseImporter
from data.db import AsyncSessionLocal
from data.repositories.cot_repo import COTRepository
from config.settings import settings
from utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)

# Nasdaq Data Link (formerly Quandl) — CFTC COT data
NASDAQ_BASE = "https://data.nasdaq.com/api/v3/datasets/CFTC"
GOLD_DATASET = "088691_FO_L_ALL"  # COMEX Gold Futures — Legacy Combined


class COTImporter(BaseImporter):
    source_name = "cot"
    run_interval = 604800  # weekly

    async def fetch(self) -> dict:
        async with aiohttp.ClientSession() as http:
            return await async_retry_with_backoff(
                self._fetch_cot, http,
                max_attempts=4, base_delay=2.0,
            )

    async def _fetch_cot(self, http: aiohttp.ClientSession) -> dict:
        url = f"{NASDAQ_BASE}/{GOLD_DATASET}.json"
        params = {"api_key": settings.nasdaq_api_key, "rows": 260}
        async with http.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def parse(self, raw: dict) -> list[dict]:
        dataset = raw.get("dataset", {})
        col_names = dataset.get("column_names", [])
        data_rows = dataset.get("data", [])
        market_name = dataset.get("name", "GOLD_COT")

        records = []
        prev_net = None
        for row in reversed(data_rows):
            row_dict = dict(zip(col_names, row))
            try:
                report_date = date.fromisoformat(row_dict["Date"])
                comm_long = int(row_dict.get("Commercial Long", 0) or 0)
                comm_short = int(row_dict.get("Commercial Short", 0) or 0)
                noncomm_long = int(row_dict.get("Noncommercial Long", 0) or 0)
                noncomm_short = int(row_dict.get("Noncommercial Short", 0) or 0)
                oi = int(row_dict.get("Open Interest", 0) or 0)
                net = noncomm_long - noncomm_short
                delta = net - prev_net if prev_net is not None else 0
                prev_net = net
                records.append({
                    "report_date": report_date,
                    "market_name": market_name,
                    "comm_long": comm_long,
                    "comm_short": comm_short,
                    "noncomm_long": noncomm_long,
                    "noncomm_short": noncomm_short,
                    "net_noncomm": net,
                    "net_noncomm_delta_wow": delta,
                    "open_interest": oi,
                })
            except (KeyError, ValueError, TypeError):
                continue
        return records

    async def store(self, data: list[dict]) -> int:
        async with AsyncSessionLocal() as session:
            repo = COTRepository(session)
            for rec in data:
                await repo.upsert(rec)
        return len(data)
