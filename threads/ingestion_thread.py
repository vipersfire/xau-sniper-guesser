import asyncio
import logging
from threads.base_thread import BaseThread

logger = logging.getLogger(__name__)


class IngestionThread(BaseThread):
    tick_interval = 60.0  # check sources every 60s
    name = "ingestion"

    def __init__(self):
        super().__init__(self.name)
        from ingestion.manager import IngestionManager
        self._manager = IngestionManager()
        self._loop = asyncio.new_event_loop()

    def run_cycle(self):
        self._loop.run_until_complete(self._manager.run_all())

    def on_stop(self):
        self._loop.close()

    def extra_status(self):
        return {"sources": self._manager.source_names}
