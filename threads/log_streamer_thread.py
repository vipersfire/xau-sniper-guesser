import logging
import time
from pathlib import Path
from threads.base_thread import BaseThread
from config.settings import settings

logger = logging.getLogger(__name__)


class LogStreamerThread(BaseThread):
    tick_interval = 2.0
    name = "log_streamer"

    def __init__(self):
        super().__init__(self.name)
        self._log_path = Path(settings.log_dir) / "xauusd_sniper.log"
        self._position = 0

    def on_start(self):
        if self._log_path.exists():
            self._position = self._log_path.stat().st_size

    def run_cycle(self):
        if not self._log_path.exists():
            return
        try:
            with open(self._log_path) as f:
                f.seek(self._position)
                new_lines = f.read()
                self._position = f.tell()
            if new_lines:
                # In a future Textual upgrade, push to live panel
                pass
        except Exception:
            pass
