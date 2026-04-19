import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from config.settings import settings

console = Console()
LOG_DIR = Path(settings.log_dir)


def show():
    while True:
        console.print("\n[bold cyan]── Logs ──[/bold cyan]")
        console.print(" 1. Tail live logs")
        console.print(" 2. Filter by module")
        console.print(" 3. List log files")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _tail_live()
        elif choice == "2":
            _filter_module()
        elif choice == "3":
            _list_files()


def _tail_live():
    log_file = LOG_DIR / "xauusd_sniper.log"
    if not log_file.exists():
        console.print(f"[dim]Log file not found: {log_file}[/dim]"); return
    console.print("[dim]Press Ctrl+C to stop tailing.[/dim]")
    try:
        subprocess.run(["tail", "-f", str(log_file)])
    except KeyboardInterrupt:
        pass


def _filter_module():
    module = Prompt.ask("Module name (e.g. ingestion, regime)")
    log_file = LOG_DIR / "xauusd_sniper.log"
    if not log_file.exists():
        console.print("[dim]No log file.[/dim]"); return
    console.print(f"[dim]Filtering for '{module}'...[/dim]")
    try:
        subprocess.run(["grep", "-i", module, str(log_file)])
    except KeyboardInterrupt:
        pass


def _list_files():
    if not LOG_DIR.exists():
        console.print("[dim]Log directory not found.[/dim]"); return
    files = sorted(LOG_DIR.glob("*.log"))
    for f in files:
        size = f.stat().st_size
        console.print(f"  {f.name}  ({size // 1024} KB)")
