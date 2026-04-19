from datetime import datetime, timezone, time
from config.constants import SESSION_WINDOWS


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def current_session(dt: datetime | None = None) -> str:
    dt = dt or utcnow()
    h = dt.hour
    sessions = []
    for name, (start, end) in SESSION_WINDOWS.items():
        if start <= h < end:
            sessions.append(name)
    if "overlap" in sessions:
        return "overlap"
    for priority in ("ny", "london", "asian"):
        if priority in sessions:
            return priority
    return "off_hours"


def is_market_open(dt: datetime | None = None) -> bool:
    dt = dt or utcnow()
    # Forex market open Mon 00:00 UTC – Fri 21:00 UTC
    if dt.weekday() == 5:  # Saturday
        return False
    if dt.weekday() == 4 and dt.hour >= 21:  # Friday after 21:00
        return False
    return True


def bar_open_time(dt: datetime, timeframe_seconds: int) -> datetime:
    ts = int(dt.timestamp())
    bar_ts = (ts // timeframe_seconds) * timeframe_seconds
    return datetime.fromtimestamp(bar_ts, tz=timezone.utc)


def seconds_until_bar_close(dt: datetime, timeframe_seconds: int) -> float:
    bar_start = bar_open_time(dt, timeframe_seconds)
    bar_end_ts = bar_start.timestamp() + timeframe_seconds
    return bar_end_ts - dt.timestamp()
