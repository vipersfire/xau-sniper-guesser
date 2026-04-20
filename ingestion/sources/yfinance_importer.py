"""yfinance importer — fetches daily/hourly bars for free market data.

IMPORTANT: yfinance data is for analysis only — never use for real-time trade signals.
Symbols: GC=F (gold futures), ^VIX (vol index), DX-Y.NYB (DXY), ^TNX (10yr yield), ^TYX (30yr yield).
"""
import asyncio
import logging
from datetime import datetime, timezone
from ingestion.base.importer import BaseImporter
from data.db import AsyncSessionLocal
from data.repositories.ohlcv_repo import OHLCVRepository

logger = logging.getLogger(__name__)

YFINANCE_SYMBOLS = {
    "GC=F":      "Gold Futures (COMEX)",
    "^VIX":      "CBOE Volatility Index",
    "DX-Y.NYB":  "US Dollar Index",
    "^TNX":      "10-Year Treasury Yield",
    "^TYX":      "30-Year Treasury Yield",
}

# Fetch 1 year of daily bars on each run
DAILY_PERIOD = "1y"
DAILY_INTERVAL = "1d"


class YFinanceImporter(BaseImporter):
    source_name = "yfinance"
    run_interval = 86400  # daily

    async def fetch(self) -> dict[str, list[dict]]:
        """Run yfinance downloads in a thread pool (yfinance is sync)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_sync)

    def _fetch_sync(self) -> dict[str, list[dict]]:
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance not installed — run: pip install yfinance")
            return {}

        results: dict[str, list[dict]] = {}
        for symbol in YFINANCE_SYMBOLS:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=DAILY_PERIOD, interval=DAILY_INTERVAL, auto_adjust=True)
                if hist.empty:
                    logger.warning("yfinance: no data for %s", symbol)
                    continue
                rows = []
                for ts, row in hist.iterrows():
                    rows.append({
                        "timestamp": ts.to_pydatetime().replace(tzinfo=timezone.utc),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": float(row.get("Volume", 0) or 0),
                    })
                results[symbol] = rows
                logger.debug("yfinance: %d bars for %s", len(rows), symbol)
            except Exception as e:
                logger.warning("yfinance fetch failed for %s: %s", symbol, e)
        return results

    async def parse(self, raw: dict[str, list[dict]]) -> dict[str, list[dict]]:
        return raw

    async def store(self, data: dict[str, list[dict]]) -> int:
        total = 0
        async with AsyncSessionLocal() as session:
            repo = OHLCVRepository(session)
            for symbol, bars in data.items():
                # Use "D1" as the timeframe tag for daily bars
                for bar in bars:
                    await repo.upsert_bars(symbol, "D1", [bar])
                    total += 1
        return total
