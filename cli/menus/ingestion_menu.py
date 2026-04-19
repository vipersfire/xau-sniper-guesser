import asyncio
from rich.console import Console
from rich.prompt import Prompt

console = Console()

SOURCES = ["fred", "cot", "oanda_sentiment", "forexfactory", "mt5_ohlcv", "kitco_rss", "reuters_rss"]


def show(ingestion_manager=None):
    while True:
        console.print("\n[bold cyan]── Data Ingestion ──[/bold cyan]")
        console.print(" 1. Run all sources (once)")
        console.print(" 2. Run specific source")
        console.print(" 3. Start continuous ingestion")
        console.print(" 4. Stop continuous ingestion")
        console.print(" 5. Last run summary")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4","5"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _run_all(ingestion_manager)
        elif choice == "2":
            _run_specific(ingestion_manager)
        elif choice == "3":
            _start_continuous(ingestion_manager)
        elif choice == "4":
            _stop_continuous(ingestion_manager)
        elif choice == "5":
            _show_summary(ingestion_manager)


def _run_all(mgr):
    if not mgr:
        console.print("[red]Ingestion manager not available.[/red]"); return
    console.print("[dim]Running all importers...[/dim]")
    results = asyncio.run(mgr.run_all())
    for r in results:
        icon = "[green]✓[/green]" if r.success else "[red]✗[/red]"
        console.print(f" {icon} {r.source}: {r.records_written} records" if r.success else f" {icon} {r.source}: {r.error}")


def _run_specific(mgr):
    if not mgr:
        console.print("[red]Ingestion manager not available.[/red]"); return
    for i, s in enumerate(SOURCES, 1):
        console.print(f" {i}. {s}")
    idx = Prompt.ask("Source #", default="1")
    try:
        source = SOURCES[int(idx) - 1]
        result = asyncio.run(mgr.run_source(source))
        if result:
            icon = "[green]✓[/green]" if result.success else "[red]✗[/red]"
            console.print(f"{icon} {result.source}: {result.records_written if result.success else result.error}")
    except (IndexError, ValueError):
        console.print("[red]Invalid selection.[/red]")


def _start_continuous(mgr):
    if not mgr:
        console.print("[red]Ingestion manager not available.[/red]"); return
    asyncio.run(mgr.start_continuous())
    console.print("[green]Continuous ingestion started.[/green]")


def _stop_continuous(mgr):
    if not mgr:
        console.print("[red]Ingestion manager not available.[/red]"); return
    asyncio.run(mgr.stop_continuous())
    console.print("[yellow]Continuous ingestion stopped.[/yellow]")


def _show_summary(mgr):
    if not mgr:
        console.print("[red]Ingestion manager not available.[/red]"); return
    health = mgr.health_summary()
    from cli.display.renderer import print_ingestion_summary
    print_ingestion_summary(health)
