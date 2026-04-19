"""MT5 candle close event subscription."""
import logging
import threading
import time
from datetime import datetime, timezone
from config.constants import TIMEFRAME_SECONDS

logger = logging.getLogger(__name__)


class CandleFeed:
    """Polls MT5 for candle closes and fires callbacks."""

    def __init__(self, symbol: str, timeframes: list[str]):
        self._symbol = symbol
        self._timeframes = timeframes
        self._callbacks: list = []
        self._running = False
        self._last_bar_time: dict[str, int] = {}

    def on_candle_close(self, callback):
        self._callbacks.append(callback)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        from mt5.adapter import MT5Adapter
        adapter = MT5Adapter()
        adapter.connect()
        while self._running:
            for tf in self._timeframes:
                bars = adapter.get_ohlcv(self._symbol, tf, bars=2)
                if not bars:
                    continue
                last_bar_time = bars[-1]["time"]
                prev = self._last_bar_time.get(tf, 0)
                if last_bar_time != prev:
                    self._last_bar_time[tf] = last_bar_time
                    if prev > 0:
                        # New bar closed
                        closed_bar = bars[-1]
                        for cb in self._callbacks:
                            try:
                                cb(tf, closed_bar)
                            except Exception as e:
                                logger.error("Candle callback error: %s", e)
            time.sleep(5)  # Poll every 5s
        adapter.disconnect()
