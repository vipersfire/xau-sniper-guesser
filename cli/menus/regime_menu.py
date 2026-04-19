from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def show(regime_monitor=None):
    while True:
        console.print("\n[bold cyan]── Regime Monitor ──[/bold cyan]")
        console.print(" 1. Current regime + confidence")
        console.print(" 2. Feature vector snapshot")
        console.print(" 3. Regime history (last 24h)")
        console.print(" 4. Anomaly score live")
        console.print(" 0. Back")

        choice = Prompt.ask("Select", choices=["0","1","2","3","4"], default="0")

        if choice == "0":
            return
        elif choice == "1":
            _current_regime(regime_monitor)
        elif choice == "2":
            _feature_vector(regime_monitor)
        elif choice == "3":
            _regime_history(regime_monitor)
        elif choice == "4":
            _anomaly_live(regime_monitor)


def _current_regime(rm):
    if not rm:
        console.print("[dim]Regime monitor not running.[/dim]"); return
    state = rm.current_state() if hasattr(rm, "current_state") else {}
    from cli.display.renderer import print_regime_panel
    print_regime_panel(
        state.get("regime_type", "unknown"),
        state.get("confidence", 0.0),
        state.get("anomaly_score", 0.0),
    )


def _feature_vector(rm):
    if not rm or not hasattr(rm, "last_features"):
        console.print("[dim]No feature data.[/dim]"); return
    features = rm.last_features or {}
    t = Table(title="Feature Vector")
    t.add_column("Feature"); t.add_column("Value", justify="right")
    for k, v in features.items():
        t.add_row(str(k), f"{v:.4f}" if isinstance(v, float) else str(v))
    console.print(t)


def _regime_history(rm):
    if not rm or not hasattr(rm, "history"):
        console.print("[dim]No history.[/dim]"); return
    history = rm.history[-48:]  # last 48 entries
    t = Table(title="Regime History (last 24h)")
    t.add_column("Time"); t.add_column("Regime"); t.add_column("Conf")
    for entry in history:
        t.add_row(
            str(entry.get("time", "")),
            entry.get("regime_type", "?"),
            f"{entry.get('confidence', 0):.0%}",
        )
    console.print(t)


def _anomaly_live(rm):
    if not rm or not hasattr(rm, "last_anomaly_score"):
        console.print("[dim]No anomaly data.[/dim]"); return
    score = rm.last_anomaly_score or 0.0
    color = "green" if score < 0.3 else "yellow" if score < 0.6 else "red"
    console.print(f"Anomaly score: [{color}]{score:.4f}[/{color}]")
