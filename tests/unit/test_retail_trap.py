"""Unit tests for engine/signals/retail_trap.py"""
import pytest
from engine.signals.retail_trap import detect_retail_traps, latest_trap_score, SWEEP_LOOKBACK


def _bar(high: float, low: float, open_: float = None, close: float = None) -> dict:
    if open_ is None:
        open_ = (high + low) / 2
    if close is None:
        close = (high + low) / 2
    return {"open": open_, "high": high, "low": low, "close": close}


def _flat_bars(n: int, price: float = 1900.0) -> list[dict]:
    """Bars with tiny range — neither SL nor TP hit."""
    return [_bar(price + 0.05, price - 0.05, price, price) for _ in range(n)]


class TestDetectRetailTraps:
    def test_no_signals_for_flat_bars(self):
        bars = _flat_bars(SWEEP_LOOKBACK + 5)
        assert detect_retail_traps(bars) == []

    def test_insufficient_bars_returns_empty(self):
        assert detect_retail_traps(_flat_bars(SWEEP_LOOKBACK - 1)) == []

    def test_bull_trap_detected(self):
        # Build SWEEP_LOOKBACK bars with high=1905, then one bar that sweeps above and rejects down.
        base = _flat_bars(SWEEP_LOOKBACK, price=1900.0)
        # Sweep bar: high > 1905 (prev_high), closes below prev_high with big upper wick
        sweep_bar = _bar(high=1910, low=1895, open_=1900, close=1897)
        bars = base + [sweep_bar]
        signals = detect_retail_traps(bars)
        assert len(signals) == 1
        assert signals[0].direction == "bull_trap"
        assert signals[0].swept_level == pytest.approx(1900.05)  # prev high from flat bars

    def test_bear_trap_detected(self):
        base = _flat_bars(SWEEP_LOOKBACK, price=1900.0)
        # Sweep bar: low < 1899.95 (prev_low), closes above prev_low with big lower wick
        sweep_bar = _bar(high=1905, low=1890, open_=1900, close=1902)
        bars = base + [sweep_bar]
        signals = detect_retail_traps(bars)
        assert len(signals) == 1
        assert signals[0].direction == "bear_trap"

    def test_weak_rejection_not_detected(self):
        """Wick less than MIN_REJECTION_RATIO → not a trap."""
        base = _flat_bars(SWEEP_LOOKBACK, price=1900.0)
        # Sweeps the prev_high (1900.05) but closes near the top — tiny upper wick
        # high=1910, low=1900 (above prev_low 1899.95 so no bear sweep)
        # open_=1909, close=1900: upper_wick=1910-1909=1, range=10 → rejection=0.10 < 0.60
        sweep_bar = _bar(high=1910, low=1900, open_=1909, close=1900)
        bars = base + [sweep_bar]
        assert detect_retail_traps(bars) == []

    def test_bar_index_matches_position(self):
        base = _flat_bars(SWEEP_LOOKBACK, price=1900.0)
        sweep_bar = _bar(high=1910, low=1895, open_=1900, close=1897)
        bars = base + [sweep_bar]
        signals = detect_retail_traps(bars)
        assert signals[0].bar_index == len(bars) - 1


class TestLatestTrapScore:
    def test_no_bars_returns_zero(self):
        assert latest_trap_score([]) == 0.0

    def test_no_recent_trap_returns_zero(self):
        bars = _flat_bars(SWEEP_LOOKBACK + 5)
        assert latest_trap_score(bars) == 0.0

    def test_recent_trap_returns_nonzero(self):
        base = _flat_bars(SWEEP_LOOKBACK, price=1900.0)
        sweep_bar = _bar(high=1910, low=1895, open_=1900, close=1897)
        bars = base + [sweep_bar]
        score = latest_trap_score(bars, lookback=3)
        assert 0 < score <= 1.0
