from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from threads.base_thread import ThreadStatus, ThreadState
from cli.display.formatters import fmt_age, fmt_datetime

console = Console()


def print_header(title: str):
    console.rule(f"[bold cyan]{title}[/bold cyan]")


def print_thread_table(statuses: list[ThreadStatus]):
    table = Table(title="Thread Status", box=box.SIMPLE_HEAVY)
    table.add_column("Thread", style="cyan")
    table.add_column("State")
    table.add_column("Cycles", justify="right")
    table.add_column("Last Cycle")
    table.add_column("Error", style="red dim")

    for s in statuses:
        state_color = {
            ThreadState.RUNNING: "green",
            ThreadState.PAUSED:  "yellow",
            ThreadState.STOPPED: "dim",
            ThreadState.ERROR:   "red",
            ThreadState.IDLE:    "dim",
        }.get(s.state, "white")
        table.add_row(
            s.name,
            f"[{state_color}]{s.state.value}[/{state_color}]",
            str(s.cycle_count),
            fmt_age(s.last_cycle_at),
            (s.last_error or "")[:60],
        )
    console.print(table)


def print_ingestion_summary(health: dict):
    table = Table(title="Ingestion Health", box=box.SIMPLE_HEAVY)
    table.add_column("Source", style="cyan")
    table.add_column("Last Run")
    table.add_column("Status")
    table.add_column("Error", style="red dim")

    for source, info in health.items():
        status = "[green]✓[/green]" if info.get("last_success") else "[red]✗[/red]"
        table.add_row(
            source,
            info.get("last_run") or "never",
            status,
            (info.get("error") or "")[:60],
        )
    console.print(table)


def print_regime_panel(regime_type: str, confidence: float, anomaly_score: float):
    text = Text()
    text.append(f"Regime:  ", style="dim")
    text.append(f"{regime_type}\n", style="bold yellow")
    color = "green" if confidence >= 0.70 else "yellow" if confidence >= 0.55 else "red"
    text.append(f"Conf:    ", style="dim")
    text.append(f"{confidence:.1%}\n", style=f"bold {color}")
    a_color = "green" if anomaly_score < 0.3 else "yellow" if anomaly_score < 0.6 else "red"
    text.append(f"Anomaly: ", style="dim")
    text.append(f"{anomaly_score:.3f}", style=f"bold {a_color}")
    console.print(Panel(text, title="Regime Monitor", border_style="cyan"))
