import logging
from threads.base_thread import BaseThread
from ota.watcher import OTAWatcher
from ota.staging import apply_params_update
from config.settings import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class OTAWatcherThread(BaseThread):
    tick_interval = 5.0
    name = "ota_watcher"

    def __init__(self, trading_engine=None):
        super().__init__(self.name)
        self._engine = trading_engine
        params_path = settings.ota_strategy_params_path
        self._watcher = OTAWatcher(
            watch_paths=[params_path],
            on_change_callback=self._on_change,
        )

    def on_start(self):
        self._watcher.start()

    def on_stop(self):
        self._watcher.stop()

    def run_cycle(self):
        pass  # OTAWatcher runs its own thread

    def _on_change(self, path: Path):
        if path.suffix == ".json":
            apply_params_update(path, self._engine)
        elif path.suffix == ".py":
            from ota.staging import apply_module_update
            module_name = path.stem.replace("/", ".")
            apply_module_update(path, module_name, self._engine)
