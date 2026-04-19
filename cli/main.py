"""XAUUSD Sniper — main CLI entry point."""
import asyncio
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from cli.menus import trading_menu, ingestion_menu, regime_menu, backtest_menu, system_menu, stats_menu, logs_menu
from cli.display.renderer import print_header

app = typer.Typer(name="xau-sniper", help="XAUUSD Sniper Trading System")
console = Console()

_thread_manager = None
_trading_engine = None
_ingestion_manager = None


def _setup_logging():
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)-24s %(levelname)-8s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "xauusd_sniper.log"),
        ],
    )


def _main_menu():
    while True:
        print_header("XAUUSD SNIPER")
        console.print("\n[bold]MAIN MENU[/bold]")
        console.print(" 1. Trading Engine")
        console.print(" 2. Data Ingestion")
        console.print(" 3. Regime Monitor")
        console.print(" 4. Backtest")
        console.print(" 5. Portfolio Stats")
        console.print(" 6. System")
        console.print(" 7. Logs")
        console.print(" q. Quit")

        choice = Prompt.ask("Select", default="q")

        if choice in ("q", "Q", "0"):
            _shutdown()
            break
        elif choice == "1":
            trading_menu.show(_thread_manager, _trading_engine)
        elif choice == "2":
            ingestion_menu.show(_ingestion_manager)
        elif choice == "3":
            regime_menu.show()
        elif choice == "4":
            backtest_menu.show()
        elif choice == "5":
            stats_menu.show()
        elif choice == "6":
            system_menu.show(_thread_manager)
        elif choice == "7":
            logs_menu.show()


def _shutdown():
    global _thread_manager
    console.print("\n[dim]Shutting down...[/dim]")
    if _thread_manager:
        _thread_manager.stop_all(wait=True)
    console.print("[dim]Goodbye.[/dim]")


@app.command()
def run():
    """Start the interactive trading terminal."""
    _setup_logging()
    _main_menu()


@app.command()
def preflight():
    """Run preflight checks and exit."""
    _setup_logging()
    from preflight.checker import PreflightChecker
    from preflight.report import render_preflight_report
    checker = PreflightChecker()
    results = asyncio.run(checker.run())
    passed = render_preflight_report(results)
    raise SystemExit(0 if passed else 1)


@app.command()
def ingest(source: str = typer.Option("all", "--source", "-s", help="Source name or 'all'")):
    """Run data ingestion."""
    _setup_logging()
    from ingestion.manager import IngestionManager
    mgr = IngestionManager()
    if source == "all":
        asyncio.run(mgr.run_all())
    else:
        asyncio.run(mgr.run_source(source))


@app.command()
def backtest(train: bool = typer.Option(False, "--train", help="Also train model after backtest")):
    """Run backtest and optionally train model."""
    _setup_logging()
    from backtest.runner import BacktestRunner
    from backtest.report import print_backtest_report
    runner = BacktestRunner()
    results = asyncio.run(runner.run_full())
    print_backtest_report(results)
    if train:
        from models.trainer import ModelTrainer
        trainer = ModelTrainer()
        asyncio.run(trainer.train())
        console.print("[green]Model trained and saved.[/green]")


@app.command()
def init_db():
    """Initialize the database schema."""
    _setup_logging()
    from data.db import init_db as _init_db
    asyncio.run(_init_db())
    console.print("[green]Database initialized.[/green]")


if __name__ == "__main__":
    app()
