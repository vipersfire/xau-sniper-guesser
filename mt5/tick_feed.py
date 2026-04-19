"""MT5 tick stream — execution only, not used for ML."""
import logging
import threading
import time

logger = logging.getLogger(__name__)


class TickFeed:
    def __init__(self, symbol: str):
        self._symbol = symbol
        self._callbacks: list = []
        self._running = False

    def on_tick(self, callback):
        self._callbacks.append(callback)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._stream, daemon=True, name="tick_feed")
        t.start()

    def stop(self):
        self._running = False

    def _stream(self):
        from mt5.adapter import MT5Adapter
        adapter = MT5Adapter()
        adapter.connect()
        while self._running:
            tick = adapter.get_tick(self._symbol)
            if tick:
                for cb in self._callbacks:
                    try:
                        cb(tick)
                    except Exception as e:
                        logger.error("Tick callback error: %s", e)
            time.sleep(0.1)  # ~10 ticks/sec
        adapter.disconnect()
