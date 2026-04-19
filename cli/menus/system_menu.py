import asyncio
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def show(thread_manager=None):
    while True:
        console.print("\n[bold cyan]── System ──[/bold cyan]")
        console.print(" 1. Preflight check")
        console.print(" 2. Thread status")
        console.print(" 3. OTA status")
        console.print(" 4. Model registry info")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _preflight()
        elif choice == "2":
            _thread_status(thread_manager)
        elif choice == "3":
            _ota_status()
        elif choice == "4":
            _model_info()


def _preflight():
    from preflight.checker import PreflightChecker
    from preflight.report import render_preflight_report
    console.print("[dim]Running preflight checks...[/dim]")
    checker = PreflightChecker(skip_broker=False)
    results = asyncio.run(checker.run())
    render_preflight_report(results)


def _thread_status(tm):
    if not tm:
        console.print("[dim]Thread manager not initialized.[/dim]"); return
    from cli.display.renderer import print_thread_table
    print_thread_table(tm.status_all())


def _ota_status():
    try:
        from ota.watcher import get_ota_status
        status = get_ota_status()
        console.print(f"OTA last reload: [cyan]{status.get('last_reload', 'never')}[/cyan]")
        console.print(f"Watched path:    [dim]{status.get('watch_path', '?')}[/dim]")
    except Exception as e:
        console.print(f"[dim]OTA status unavailable: {e}[/dim]")


def _model_info():
    from models.registry import ModelRegistry
    registry = ModelRegistry()
    info = registry.check()
    if info.valid:
        console.print(f"[green]✓[/green] Model: {info.path.name}")
        console.print(f"  Trained: [cyan]{info.trained_at}[/cyan]")
    else:
        console.print(f"[red]✗[/red] Model: {info.error}")
