import asyncio
import logging
from ingestion.base.scheduler import ImportScheduler
from ingestion.sources.fred_importer import FREDImporter
from ingestion.sources.cot_importer import COTImporter
from ingestion.sources.yfinance_importer import YFinanceImporter
from ingestion.sources.forexfactory_importer import ForexFactoryImporter
from ingestion.sources.mt5_ohlcv_importer import MT5OHLCVImporter
from ingestion.sources.kitco_rss_importer import KitcoRSSImporter
from ingestion.sources.reuters_rss_importer import ReutersRSSImporter

logger = logging.getLogger(__name__)


class IngestionManager:
    """Top-level orchestrator for all data ingestion."""

    def __init__(self):
        self.scheduler = ImportScheduler()
        self._setup_importers()

    def _setup_importers(self):
        self.scheduler.register(FREDImporter())
        self.scheduler.register(COTImporter())
        self.scheduler.register(YFinanceImporter())
        self.scheduler.register(ForexFactoryImporter())
        self.scheduler.register(MT5OHLCVImporter())
        self.scheduler.register(KitcoRSSImporter())
        self.scheduler.register(ReutersRSSImporter())

    async def run_all(self):
        results = await self.scheduler.run_all_once()
        for r in results:
            if r.success:
                logger.info("✓ %s: %d records", r.source, r.records_written)
            else:
                logger.error("✗ %s: %s", r.source, r.error)
        return results

    async def run_source(self, source_name: str):
        return await self.scheduler.run_source_once(source_name)

    async def start_continuous(self):
        await self.scheduler.start_continuous()

    async def stop_continuous(self):
        await self.scheduler.stop_continuous()

    def health_summary(self) -> dict:
        return self.scheduler.health_summary()

    @property
    def source_names(self) -> list[str]:
        return self.scheduler.source_names
