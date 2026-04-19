import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    source: str
    success: bool
    records_written: int = 0
    error: str | None = None
    ran_at: datetime = None

    def __post_init__(self):
        if self.ran_at is None:
            self.ran_at = datetime.utcnow()


class BaseImporter(ABC):
    source_name: str = "base"
    run_interval: int = 3600  # seconds between runs

    def __init__(self):
        self.logger = logging.getLogger(f"ingestion.{self.source_name}")
        self._last_run: datetime | None = None
        self._last_result: ImportResult | None = None

    @abstractmethod
    async def fetch(self) -> Any:
        """Fetch raw data from source."""
        ...

    @abstractmethod
    async def parse(self, raw: Any) -> Any:
        """Parse raw data into clean structured form."""
        ...

    @abstractmethod
    async def store(self, data: Any) -> int:
        """Persist clean data. Returns number of records written."""
        ...

    async def run_once(self) -> ImportResult:
        self.logger.info("Running %s importer", self.source_name)
        try:
            raw = await self.fetch()
            clean = await self.parse(raw)
            n = await self.store(clean)
            result = ImportResult(source=self.source_name, success=True, records_written=n)
        except Exception as e:
            self.logger.exception("Importer %s failed: %s", self.source_name, e)
            result = ImportResult(source=self.source_name, success=False, error=str(e))
        self._last_run = datetime.utcnow()
        self._last_result = result
        return result

    async def run_loop(self):
        """Continuous mode — runs until task is cancelled."""
        import asyncio
        while True:
            await self.run_once()
            self.logger.debug("%s sleeping %ds", self.source_name, self.run_interval)
            await asyncio.sleep(self.run_interval)

    async def health_check(self) -> bool:
        if self._last_result is None:
            return True  # never run yet — not unhealthy
        return self._last_result.success

    @property
    def last_result(self) -> ImportResult | None:
        return self._last_result

    @property
    def last_run(self) -> datetime | None:
        return self._last_run
