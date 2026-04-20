"""CFTC COT importer — downloads directly from cftc.gov ZIP CSV (no API key needed)."""
import io
import csv
import zipfile
import logging
import asyncio
from datetime import date

logger = logging.getLogger(__name__)

# CFTC public ZIP CSV base URL — one file per year
CFTC_BASE_URL = "https://www.cftc.gov/dta/zip/deacot{year}.zip"

# COMEX Gold Futures market code
GOLD_MARKET_CODE = "088691"
GOLD_MARKET_NAME = "GOLD - COMMODITY EXCHANGE INC."

# How many prior years to backfill on first run (current year included separately)
BACKFILL_YEARS = 4


def _current_year() -> int:
    return date.today().year


class COTImporter:  # BaseImporter imported lazily to avoid heavy deps at test time
    source_name = "cot"
    run_interval = 604800  # weekly

    async def fetch(self) -> list[dict]:
        """Fetch COT data for current + backfill years."""
        import aiohttp
        from utils.retry import async_retry_with_backoff

        async with aiohttp.ClientSession() as http:
            all_rows: list[dict] = []
            years = list(range(_current_year() - BACKFILL_YEARS, _current_year() + 1))
            for year in years:
                try:
                    rows = await async_retry_with_backoff(
                        self._fetch_year, http, year,
                        max_attempts=4, base_delay=2.0,
                    )
                    all_rows.extend(rows)
                    logger.debug("COT fetched %d rows for %d", len(rows), year)
                except Exception as e:
                    logger.warning("COT fetch failed for %d: %s", year, e)
            return all_rows

    async def _fetch_year(self, http, year: int) -> list[dict]:
        import aiohttp
        url = CFTC_BASE_URL.format(year=year)
        async with http.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()
            data = await resp.read()
        return _parse_cot_zip(data)

    async def parse(self, raw: list[dict]) -> list[dict]:
        return raw

    async def store(self, data: list[dict]) -> int:
        from data.db import AsyncSessionLocal
        from data.repositories.cot_repo import COTRepository
        async with AsyncSessionLocal() as session:
            repo = COTRepository(session)
            for rec in data:
                await repo.upsert(rec)
        return len(data)

    async def run_once(self):
        """Standalone run: fetch → parse → store."""
        from ingestion.base.importer import ImportResult
        try:
            raw = await self.fetch()
            clean = await self.parse(raw)
            n = await self.store(clean)
            return ImportResult(source=self.source_name, success=True, records_written=n)
        except Exception as e:
            logger.exception("COTImporter failed: %s", e)
            from ingestion.base.importer import ImportResult
            return ImportResult(source=self.source_name, success=False, error=str(e))


def _parse_cot_zip(zip_bytes: bytes) -> list[dict]:
    """Extract and parse the CFTC annual CSV ZIP, filtering to gold rows."""
    records: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        txt_name = next((n for n in names if n.lower().endswith(".txt")), names[0] if names else None)
        if not txt_name:
            return records
        with zf.open(txt_name) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"))
            rows_by_date: list[dict] = []
            for row in reader:
                code = row.get("CFTC_Contract_Market_Code", "").strip()
                if code != GOLD_MARKET_CODE:
                    continue
                rows_by_date.append(row)

            rows_by_date.sort(key=lambda r: r.get("Report_Date_as_YYYY-MM-DD", ""))

            prev_net = 0
            for row in rows_by_date:
                try:
                    report_date = date.fromisoformat(row["Report_Date_as_YYYY-MM-DD"].strip())
                    comm_long = int(row.get("Comm_Positions_Long_All", 0) or 0)
                    comm_short = int(row.get("Comm_Positions_Short_All", 0) or 0)
                    noncomm_long = int(row.get("NonComm_Positions_Long_All", 0) or 0)
                    noncomm_short = int(row.get("NonComm_Positions_Short_All", 0) or 0)
                    oi = int(row.get("Open_Interest_All", 0) or 0)
                    net = noncomm_long - noncomm_short
                    delta = net - prev_net
                    prev_net = net
                    records.append({
                        "report_date": report_date,
                        "market_name": GOLD_MARKET_NAME,
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
