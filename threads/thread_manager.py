import logging
from threads.base_thread import BaseThread
from threads.registry import ThreadRegistry

logger = logging.getLogger(__name__)


class ThreadManager:
    """Owns and manages all application background threads."""

    def __init__(self):
        self.registry = ThreadRegistry()
        self._threads: dict[str, BaseThread] = {}

    def register(self, thread: BaseThread):
        self._threads[thread.name] = thread
        self.registry.register(thread)

    def start_all(self):
        for name, t in self._threads.items():
            try:
                t.start()
                logger.info("Started thread: %s", name)
            except Exception as e:
                logger.error("Failed to start thread %s: %s", name, e)

    def stop_all(self, wait: bool = True):
        for name, t in self._threads.items():
            try:
                if wait:
                    t.stop_and_wait()
                else:
                    t.stop()
                logger.info("Stopped thread: %s", name)
            except Exception as e:
                logger.error("Error stopping thread %s: %s", name, e)

    def start(self, name: str):
        if t := self._threads.get(name):
            t.start()

    def stop(self, name: str):
        if t := self._threads.get(name):
            t.stop()

    def pause(self, name: str):
        if t := self._threads.get(name):
            t.pause()

    def resume(self, name: str):
        if t := self._threads.get(name):
            t.resume()

    def get(self, name: str) -> BaseThread | None:
        return self._threads.get(name)

    def status_all(self):
        return self.registry.all_statuses()
