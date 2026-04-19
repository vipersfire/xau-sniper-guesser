import logging
from threads.base_thread import BaseThread

logger = logging.getLogger(__name__)


class ExecutionThread(BaseThread):
    tick_interval = 1.0
    name = "execution"

    def __init__(self, trading_engine=None):
        super().__init__(self.name)
        self._engine = trading_engine

    def run_cycle(self):
        if not self._engine:
            return
        # Position monitoring is handled via tick_watcher + engine.on_tick
        # This thread handles expiry checks
        self._check_expiry()

    def _check_expiry(self):
        if not self._engine:
            return
        import asyncio
        from datetime import datetime, timezone
        for pos in self._engine.executor.position_manager.get_all():
            # Expiry: if position is open beyond regime duration + buffer
            age_hours = (datetime.now(timezone.utc) - pos.open_time).total_seconds() / 3600
            if age_hours > 24:  # Fallback hard expiry: 24h
                logger.info("Closing expired position %d (age=%.1fh)", pos.trade_id, age_hours)
                asyncio.run(self._engine.executor.close_trade(pos.trade_id, reason="expired"))
