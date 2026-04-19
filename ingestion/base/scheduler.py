import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.base.importer import BaseImporter, ImportResult

logger = logging.getLogger(__name__)


class ImportScheduler:
    """Runs multiple importers on their individual schedules."""

    def __init__(self):
        self._importers: list["BaseImporter"] = []
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def register(self, importer: "BaseImporter"):
        self._importers.append(importer)

    async def run_all_once(self) -> list["ImportResult"]:
        results = await asyncio.gather(
            *[imp.run_once() for imp in self._importers],
            return_exceptions=False,
        )
        return list(results)

    async def run_source_once(self, source_name: str) -> "ImportResult | None":
        for imp in self._importers:
            if imp.source_name == source_name:
                return await imp.run_once()
        logger.warning("Source not found: %s", source_name)
        return None

    async def start_continuous(self):
        self._running = True
        self._tasks = [
            asyncio.create_task(self._schedule_importer(imp), name=f"importer:{imp.source_name}")
            for imp in self._importers
        ]
        logger.info("Continuous ingestion started for %d sources", len(self._importers))

    async def stop_continuous(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Continuous ingestion stopped")

    async def _schedule_importer(self, importer: "BaseImporter"):
        while self._running:
            await importer.run_once()
            await asyncio.sleep(importer.run_interval)

    def health_summary(self) -> dict:
        return {
            imp.source_name: {
                "last_run": imp.last_run.isoformat() if imp.last_run else None,
                "last_success": imp.last_result.success if imp.last_result else None,
                "error": imp.last_result.error if imp.last_result else None,
            }
            for imp in self._importers
        }

    @property
    def source_names(self) -> list[str]:
        return [imp.source_name for imp in self._importers]
