"""Unit tests for threads/base_thread.py"""
import time
import threading
import pytest
from threads.base_thread import BaseThread, ThreadState


class CountingThread(BaseThread):
    tick_interval = 0.05  # fast for tests

    def __init__(self):
        super().__init__("counting_test")
        self.cycle_count_custom = 0

    def run_cycle(self):
        self.cycle_count_custom += 1


class ErrorThread(BaseThread):
    tick_interval = 0.05

    def __init__(self):
        super().__init__("error_test")
        self.errors_seen = 0

    def run_cycle(self):
        raise ValueError("intentional test error")

    def on_error(self, e: Exception):
        self.errors_seen += 1


class TestBaseThread:
    def test_initial_state_is_idle(self):
        t = CountingThread()
        assert t.status().state == ThreadState.IDLE

    def test_start_changes_state_to_running(self):
        t = CountingThread()
        t.start()
        time.sleep(0.05)
        assert t.status().state == ThreadState.RUNNING
        t.stop_and_wait(timeout=2)

    def test_stop_changes_state(self):
        t = CountingThread()
        t.start()
        time.sleep(0.05)
        t.stop_and_wait(timeout=2)
        assert not t.is_alive()

    def test_cycles_increment(self):
        t = CountingThread()
        t.start()
        time.sleep(0.3)
        t.stop_and_wait(timeout=2)
        assert t.cycle_count_custom >= 1

    def test_pause_and_resume(self):
        t = CountingThread()
        t.start()
        time.sleep(0.1)
        t.pause()
        assert t.status().state == ThreadState.PAUSED
        count_after_pause = t.cycle_count_custom
        time.sleep(0.2)
        # Should not have incremented while paused
        assert t.cycle_count_custom == count_after_pause
        t.resume()
        time.sleep(0.15)
        assert t.cycle_count_custom > count_after_pause
        t.stop_and_wait(timeout=2)

    def test_double_start_does_not_create_duplicate(self):
        t = CountingThread()
        t.start()
        time.sleep(0.05)
        t.start()  # Should be a no-op
        time.sleep(0.05)
        t.stop_and_wait(timeout=2)
        # Only one thread should have been running
        assert not t.is_alive()

    def test_error_in_cycle_does_not_kill_thread(self):
        t = ErrorThread()
        t.start()
        time.sleep(0.3)
        assert t.is_alive()  # Thread survives errors
        assert t.errors_seen >= 1
        t.stop_and_wait(timeout=2)

    def test_status_contains_last_error(self):
        t = ErrorThread()
        t.start()
        time.sleep(0.2)
        t.stop_and_wait(timeout=2)
        status = t.status()
        assert status.last_error == "intentional test error"

    def test_status_contains_cycle_count(self):
        t = CountingThread()
        t.start()
        time.sleep(0.3)
        t.stop_and_wait(timeout=2)
        assert t.status().cycle_count >= 1
