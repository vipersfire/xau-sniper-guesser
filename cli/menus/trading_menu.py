import asyncio
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def show(thread_manager=None, trading_engine=None):
    while True:
        console.print("\n[bold cyan]── Trading Engine ──[/bold cyan]")
        console.print(" 1. Start engine")
        console.print(" 2. Stop engine")
        console.print(" 3. Pause engine")
        console.print(" 4. Current regime + confidence")
        console.print(" 5. Active positions")
        console.print(" 6. [bold red]Emergency stop all[/bold red]")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4","5","6"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _start_engine(thread_manager)
        elif choice == "2":
            _stop_engine(thread_manager)
        elif choice == "3":
            _pause_engine(thread_manager)
        elif choice == "4":
            _show_regime(trading_engine)
        elif choice == "5":
            _show_positions(trading_engine)
        elif choice == "6":
            _emergency_stop(thread_manager, trading_engine)


def _start_engine(tm):
    if tm:
        tm.start("execution")
        tm.start("regime_monitor")
        tm.start("candle_watcher")
        tm.start("tick_watcher")
        console.print("[green]Trading engine started.[/green]")
    else:
        console.print("[red]Thread manager not initialized.[/red]")


def _stop_engine(tm):
    if tm:
        for name in ("execution", "regime_monitor", "candle_watcher", "tick_watcher"):
            tm.stop(name)
        console.print("[yellow]Trading engine stopped.[/yellow]")


def _pause_engine(tm):
    if tm:
        tm.pause("execution")
        console.print("[yellow]Execution paused.[/yellow]")


def _show_regime(engine):
    if engine:
        state = engine.current_state()
        from cli.display.renderer import print_regime_panel
        print_regime_panel(
            state.get("regime_type", "unknown"),
            state.get("confidence", 0.0),
            state.get("anomaly_score", 0.0),
        )
    else:
        console.print("[dim]Engine not running.[/dim]")


def _show_positions(engine):
    if engine:
        positions = engine.open_positions()
        if not positions:
            console.print("[dim]No open positions.[/dim]")
            return
        from rich.table import Table
        t = Table()
        t.add_column("Ticket"); t.add_column("Dir"); t.add_column("Entry"); t.add_column("SL"); t.add_column("TP"); t.add_column("PnL")
        for p in positions:
            t.add_row(str(p.ticket), p.direction, f"{p.entry_price:.2f}", f"{p.sl_price:.2f}", f"{p.tp_price:.2f}", f"{p.unrealized_pnl:+.2f}")
        console.print(t)
    else:
        console.print("[dim]Engine not running.[/dim]")


def _emergency_stop(tm, engine):
    from rich.prompt import Confirm
    if not Confirm.ask("[bold red]Close ALL positions and halt? This cannot be undone.[/bold red]"):
        return
    if engine:
        engine.emergency_stop()
    if tm:
        tm.stop_all(wait=False)
    console.print("[bold red]Emergency stop executed.[/bold red]")
