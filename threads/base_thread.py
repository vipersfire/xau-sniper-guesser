import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class ThreadState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ThreadStatus:
    name: str
    state: ThreadState
    last_cycle_at: datetime | None
    last_error: str | None
    cycle_count: int
    extra: dict[str, Any] = field(default_factory=dict)


class BaseThread(ABC):
    tick_interval: float = 1.0  # seconds between run_cycle calls

    def __init__(self, name: str):
        self.name = name
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused by default
        self._state = ThreadState.IDLE
        self._last_cycle_at: datetime | None = None
        self._last_error: str | None = None
        self._cycle_count = 0

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._state = ThreadState.RUNNING
        self._thread = threading.Thread(target=self._loop, name=self.name, daemon=True)
        self._thread.start()
        logger.info("Thread started: %s", self.name)

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused
        self._state = ThreadState.STOPPED
        logger.info("Thread stop signalled: %s", self.name)

    def stop_and_wait(self, timeout: float = 10.0):
        self.stop()
        if self._thread:
            self._thread.join(timeout=timeout)

    def pause(self):
        self._pause_event.clear()
        self._state = ThreadState.PAUSED
        logger.info("Thread paused: %s", self.name)

    def resume(self):
        self._pause_event.set()
        self._state = ThreadState.RUNNING
        logger.info("Thread resumed: %s", self.name)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── status ───────────────────────────────────────────────────────────────

    def status(self) -> ThreadStatus:
        return ThreadStatus(
            name=self.name,
            state=self._state,
            last_cycle_at=self._last_cycle_at,
            last_error=self._last_error,
            cycle_count=self._cycle_count,
            extra=self.extra_status(),
        )

    def extra_status(self) -> dict[str, Any]:
        return {}

    # ── internal loop ────────────────────────────────────────────────────────

    def _loop(self):
        self.on_start()
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break
            try:
                self.run_cycle()
                self._last_cycle_at = datetime.utcnow()
                self._cycle_count += 1
            except Exception as e:
                self._last_error = str(e)
                self._state = ThreadState.ERROR
                self.on_error(e)
                self._state = ThreadState.RUNNING
            self._stop_event.wait(timeout=self.tick_interval)
        self.on_stop()

    # ── hooks ────────────────────────────────────────────────────────────────

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_error(self, e: Exception):
        logger.exception("Error in thread %s: %s", self.name, e)

    # ── abstract ─────────────────────────────────────────────────────────────

    @abstractmethod
    def run_cycle(self):
        ...
