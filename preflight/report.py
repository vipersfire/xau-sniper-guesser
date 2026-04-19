from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from preflight.checks.base_check import CheckResult

console = Console()


def render_preflight_report(results: list[CheckResult]) -> bool:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("status", style="bold", width=3)
    table.add_column("check", style="bold cyan", width=24)
    table.add_column("detail")
    table.add_column("fix", style="dim yellow")

    all_passed = True
    for r in results:
        icon = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
        fix = r.fix_command or ""
        if not r.passed:
            all_passed = False
        table.add_row(icon, r.name, r.detail, fix)

    title = "PREFLIGHT CHECK"
    border_style = "green" if all_passed else "red"
    console.print(Panel(table, title=title, border_style=border_style))

    if all_passed:
        console.print("[bold green]All checks passed. Safe to start trading engine.[/bold green]")
    else:
        console.print("[bold red]Preflight failed. Fix the issues above before starting.[/bold red]")

    return all_passed
