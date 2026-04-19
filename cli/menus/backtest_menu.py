import asyncio
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def show():
    while True:
        console.print("\n[bold cyan]── Backtest ──[/bold cyan]")
        console.print(" 1. Run full backtest (5yr)")
        console.print(" 2. Run regime-specific backtest")
        console.print(" 3. Train model (from backtest results)")
        console.print(" 4. View last results")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _run_full()
        elif choice == "2":
            _run_regime_specific()
        elif choice == "3":
            _train_model()
        elif choice == "4":
            _view_results()


def _run_full():
    console.print("[dim]Starting full backtest (this may take several minutes)...[/dim]")
    try:
        from backtest.runner import BacktestRunner
        runner = BacktestRunner()
        results = asyncio.run(runner.run_full())
        from backtest.report import print_backtest_report
        print_backtest_report(results)
    except Exception as e:
        console.print(f"[red]Backtest failed: {e}[/red]")


def _run_regime_specific():
    from engine.regime.regime_types import RegimeType
    regime_names = [r.value for r in RegimeType]
    for i, name in enumerate(regime_names, 1):
        console.print(f" {i}. {name}")
    idx = Prompt.ask("Regime #", default="1")
    try:
        regime = regime_names[int(idx) - 1]
        from backtest.runner import BacktestRunner
        runner = BacktestRunner()
        results = asyncio.run(runner.run_regime(regime))
        from backtest.report import print_backtest_report
        print_backtest_report(results)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _train_model():
    console.print("[dim]Training regime classifier...[/dim]")
    try:
        from models.trainer import ModelTrainer
        trainer = ModelTrainer()
        asyncio.run(trainer.train())
        console.print("[green]Model trained and saved.[/green]")
    except Exception as e:
        console.print(f"[red]Training failed: {e}[/red]")


def _view_results():
    try:
        from backtest.report import load_last_report, print_backtest_report
        results = load_last_report()
        if results:
            print_backtest_report(results)
        else:
            console.print("[dim]No results found. Run a backtest first.[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
