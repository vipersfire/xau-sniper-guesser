import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def print_backtest_report(results: dict):
    if "error" in results:
        console.print(f"[red]Backtest error: {results['error']}[/red]")
        return

    metrics = results.get("metrics", {})
    table = Table(title="Backtest Results", box=box.SIMPLE_HEAVY)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total trades",   str(metrics.get("total_trades", 0)))
    table.add_row("Win rate",       f"{metrics.get('win_rate', 0):.1%}")
    table.add_row("Profit factor",  f"{metrics.get('profit_factor', 0):.2f}")
    table.add_row("Expectancy",     f"{metrics.get('expectancy', 0):.2f} pips")
    table.add_row("Avg R",          f"{metrics.get('avg_r', 0):.3f}")
    table.add_row("Max drawdown",   f"{metrics.get('max_drawdown', 0):.0f} pips")
    table.add_row("Total P&L",      f"{metrics.get('total_pnl', 0):.0f} pips")
    table.add_row("Sharpe",         f"{metrics.get('sharpe', 0):.2f}")

    period = f"{results.get('start', '?')[:10]} → {results.get('end', '?')[:10]}"
    table.add_row("Period",         period)
    table.add_row("Bars",           str(results.get("bars", 0)))
    table.add_row("Signals",        str(results.get("signals", 0)))

    console.print(table)


def load_last_report() -> dict | None:
    path = Path("logs/last_backtest.json")
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)
