import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from threads.base_thread import BaseThread, ThreadStatus


class ThreadRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._threads: dict[str, "BaseThread"] = {}

    def register(self, thread: "BaseThread"):
        with self._lock:
            self._threads[thread.name] = thread

    def unregister(self, name: str):
        with self._lock:
            self._threads.pop(name, None)

    def get(self, name: str) -> "BaseThread | None":
        return self._threads.get(name)

    def all_statuses(self) -> list["ThreadStatus"]:
        with self._lock:
            return [t.status() for t in self._threads.values()]

    def all_names(self) -> list[str]:
        with self._lock:
            return list(self._threads.keys())

    def alive_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._threads.values() if t.is_alive())
