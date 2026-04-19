import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def show():
    while True:
        console.print("\n[bold cyan]── Portfolio Stats ──[/bold cyan]")
        console.print(" 1. Today's P&L")
        console.print(" 2. Win rate by regime")
        console.print(" 3. R-multiple distribution")
        console.print(" 4. Drawdown report")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _today_pnl()
        elif choice == "2":
            _win_rate_regime()
        elif choice == "3":
            _r_multiple()
        elif choice == "4":
            _drawdown()


def _today_pnl():
    try:
        from data.db import AsyncSessionLocal
        from data.repositories.trade_repo import TradeRepository
        async def _get():
            async with AsyncSessionLocal() as session:
                repo = TradeRepository(session)
                return await repo.total_pnl_today()
        pnl = asyncio.run(_get())
        color = "green" if pnl >= 0 else "red"
        console.print(f"Today's P&L: [{color}]{pnl:+.2f}[/{color}]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _win_rate_regime():
    try:
        from data.db import AsyncSessionLocal
        from data.repositories.trade_repo import TradeRepository
        async def _get():
            async with AsyncSessionLocal() as session:
                repo = TradeRepository(session)
                return await repo.win_rate_by_regime()
        stats = asyncio.run(_get())
        t = Table(title="Win Rate by Regime")
        t.add_column("Regime"); t.add_column("Trades", justify="right"); t.add_column("Total P&L", justify="right")
        for regime, s in stats.items():
            t.add_row(regime, str(s["count"]), f"{s['total_pnl']:+.2f}")
        console.print(t)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _r_multiple():
    try:
        from backtest.metrics import compute_r_multiple_distribution
        dist = asyncio.run(compute_r_multiple_distribution())
        console.print(f"Avg R: [cyan]{dist.get('avg_r', 0):.2f}[/cyan]")
        console.print(f"Med R: [cyan]{dist.get('median_r', 0):.2f}[/cyan]")
        console.print(f"Expectancy: [cyan]{dist.get('expectancy', 0):.2f}R[/cyan]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _drawdown():
    try:
        from data.db import AsyncSessionLocal
        from data.repositories.trade_repo import TradeRepository
        async def _get():
            async with AsyncSessionLocal() as session:
                repo = TradeRepository(session)
                return await repo.account_drawdown_24h()
        dd = asyncio.run(_get())
        color = "green" if dd < 1 else "yellow" if dd < 3 else "red"
        console.print(f"24h drawdown: [{color}]{dd:.2f}[/{color}]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
