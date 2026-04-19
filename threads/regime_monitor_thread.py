import asyncio
import logging
from threads.base_thread import BaseThread

logger = logging.getLogger(__name__)


class RegimeMonitorThread(BaseThread):
    tick_interval = 900.0  # every 15 min (M15 candle)
    name = "regime_monitor"

    def __init__(self, trading_engine=None):
        super().__init__(self.name)
        self._engine = trading_engine

    def run_cycle(self):
        if not self._engine:
            return
        state = self._engine.current_state()
        logger.debug("Regime: %s conf=%.1f%%", state.get("regime_type"), state.get("confidence", 0) * 100)
