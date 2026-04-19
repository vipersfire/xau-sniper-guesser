import asyncio
import logging
from threads.base_thread import BaseThread
from config.constants import SYMBOL, TIMEFRAMES

logger = logging.getLogger(__name__)


class CandleWatcherThread(BaseThread):
    tick_interval = 5.0
    name = "candle_watcher"

    def __init__(self, trading_engine=None):
        super().__init__(self.name)
        self._engine = trading_engine
        self._last_bar_times: dict[str, int] = {}
        self._adapter = None

    def on_start(self):
        from mt5.adapter import MT5Adapter
        self._adapter = MT5Adapter()
        self._adapter.connect()
        logger.info("CandleWatcher connected to MT5")

    def on_stop(self):
        if self._adapter:
            self._adapter.disconnect()

    def run_cycle(self):
        if not self._adapter or not self._engine:
            return
        for tf in TIMEFRAMES:
            bars = self._adapter.get_ohlcv(SYMBOL, tf, bars=2)
            if not bars:
                continue
            last_time = bars[-1]["time"]
            prev_time = self._last_bar_times.get(tf, 0)
            if last_time != prev_time and prev_time > 0:
                self._last_bar_times[tf] = last_time
                try:
                    asyncio.run(self._engine.on_candle_close(tf, bars[-1]))
                except Exception as e:
                    logger.error("Candle close handler error: %s", e)
            elif prev_time == 0:
                self._last_bar_times[tf] = last_time
