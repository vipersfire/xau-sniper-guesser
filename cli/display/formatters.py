from datetime import datetime


def fmt_price(price: float | None) -> str:
    if price is None:
        return "—"
    return f"{price:.2f}"


def fmt_pips(pips: float | None) -> str:
    if pips is None:
        return "—"
    return f"{pips:+.1f}"


def fmt_pct(pct: float | None) -> str:
    if pct is None:
        return "—"
    return f"{pct:.1f}%"


def fmt_confidence(conf: float | None) -> str:
    if conf is None:
        return "—"
    color = "green" if conf >= 0.70 else "yellow" if conf >= 0.55 else "red"
    return f"[{color}]{conf:.0%}[/{color}]"


def fmt_pnl(pnl: float | None) -> str:
    if pnl is None:
        return "—"
    color = "green" if pnl >= 0 else "red"
    return f"[{color}]{pnl:+.2f}[/{color}]"


def fmt_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_age(dt: datetime | None) -> str:
    if dt is None:
        return "never"
    delta = datetime.utcnow() - dt
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"
