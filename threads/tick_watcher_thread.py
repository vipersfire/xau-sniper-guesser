import logging
from threads.base_thread import BaseThread
from config.constants import SYMBOL

logger = logging.getLogger(__name__)


class TickWatcherThread(BaseThread):
    tick_interval = 0.1  # fast loop
    name = "tick_watcher"

    def __init__(self, trading_engine=None):
        super().__init__(self.name)
        self._engine = trading_engine
        self._adapter = None

    def on_start(self):
        from mt5.adapter import MT5Adapter
        self._adapter = MT5Adapter()
        self._adapter.connect()

    def on_stop(self):
        if self._adapter:
            self._adapter.disconnect()

    def run_cycle(self):
        if not self._adapter or not self._engine:
            return
        tick = self._adapter.get_tick(SYMBOL)
        if tick:
            self._engine.on_tick(tick)
