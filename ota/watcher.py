"""OTA FileWatcher — detects changes in watched paths via SHA256 hash comparison."""
import logging
import threading
import time
from pathlib import Path
from utils.hashing import sha256_file

logger = logging.getLogger(__name__)

_ota_status: dict = {"last_reload": None, "watch_path": None}


def get_ota_status() -> dict:
    return _ota_status


class OTAWatcher:
    def __init__(self, watch_paths: list[str], on_change_callback):
        self._paths = [Path(p) for p in watch_paths]
        self._callback = on_change_callback
        self._hashes: dict[Path, str] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        if self._paths:
            _ota_status["watch_path"] = str(self._paths[0].parent)

    def start(self):
        self._running = True
        self._hashes = self._snapshot()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="ota_watcher")
        self._thread.start()
        logger.info("OTA watcher started, watching %d paths", len(self._paths))

    def stop(self):
        self._running = False

    def _snapshot(self) -> dict[Path, str]:
        result = {}
        for p in self._paths:
            if p.exists():
                try:
                    result[p] = sha256_file(p)
                except Exception:
                    result[p] = ""
        return result

    def _watch_loop(self):
        while self._running:
            time.sleep(5)
            current = self._snapshot()
            for path, new_hash in current.items():
                old_hash = self._hashes.get(path, "")
                if new_hash != old_hash:
                    logger.info("OTA change detected: %s", path.name)
                    self._hashes[path] = new_hash
                    try:
                        self._callback(path)
                        _ota_status["last_reload"] = path.name
                    except Exception as e:
                        logger.error("OTA callback error for %s: %s", path, e)
