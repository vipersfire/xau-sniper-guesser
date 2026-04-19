from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich import box
import threading
import time

console = Console()


class StatusBar:
    """Live-updating status strip at bottom of terminal."""

    def __init__(self, thread_manager):
        self.thread_manager = thread_manager
        self._live: Live | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._live:
            self._live.stop()

    def _run(self):
        with Live(self._render(), refresh_per_second=1, console=console) as live:
            self._live = live
            while self._running:
                live.update(self._render())
                time.sleep(1)

    def _render(self) -> Table:
        statuses = self.thread_manager.status_all()
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        for s in statuses:
            color = "green" if s.state.value == "running" else "yellow" if s.state.value == "paused" else "red"
            table.add_column(s.name, style=color)
        row = [f"[{('green' if s.state.value == 'running' else 'dim')}]{s.state.value}[/]" for s in statuses]
        if row:
            table.add_row(*row)
        return table
