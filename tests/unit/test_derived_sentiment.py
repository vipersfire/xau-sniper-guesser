"""Unit tests for engine/signals/sentiment.py pure functions."""
import pytest
from engine.signals.sentiment import _range_position, _session_momentum, _cot_divergence


def _bar(high: float, low: float, open_: float, close: float) -> dict:
    return {"open": open_, "high": high, "low": low, "close": close}


class TestRangePosition:
    def test_price_at_top(self):
        bars = [_bar(1910, 1900, 1905, 1910)]
        assert _range_position(bars) == pytest.approx(1.0)

    def test_price_at_bottom(self):
        bars = [_bar(1910, 1900, 1905, 1900)]
        assert _range_position(bars) == pytest.approx(0.0)

    def test_price_at_midpoint(self):
        bars = [_bar(1910, 1900, 1905, 1905)]
        assert _range_position(bars) == pytest.approx(0.5)

    def test_empty_bars(self):
        assert _range_position([]) == 0.5

    def test_zero_range(self):
        bars = [_bar(1900, 1900, 1900, 1900)]
        assert _range_position(bars) == 0.5

    def test_clamps_to_one(self):
        # Close above the tracked high (shouldn't happen in practice but must not crash)
        bars = [_bar(1910, 1900, 1905, 1915)]
        assert _range_position(bars) == pytest.approx(1.0)


class TestSessionMomentum:
    def test_full_bullish_session(self):
        # Two-bar session: opens at 1900, closes at 1910; range = 1910 - 1895 = 15
        bars = [
            _bar(1910, 1895, 1900, 1905),
            _bar(1912, 1898, 1905, 1910),
        ]
        result = _session_momentum(bars)
        assert result > 0

    def test_bearish_session(self):
        bars = [
            _bar(1910, 1895, 1905, 1900),
            _bar(1905, 1890, 1900, 1895),
        ]
        result = _session_momentum(bars)
        assert result < 0

    def test_single_bar_returns_zero(self):
        bars = [_bar(1910, 1890, 1900, 1905)]
        assert _session_momentum(bars) == 0.0

    def test_empty_returns_zero(self):
        assert _session_momentum([]) == 0.0

    def test_zero_range_returns_zero(self):
        bars = [_bar(1900, 1900, 1900, 1900)]
        assert _session_momentum(bars) == 0.0


class TestCOTDivergence:
    def _cot(self, net: int):
        class _R:
            def __init__(self, n):
                self.net_noncomm = n
        return _R(net)

    def test_agreement_bullish(self):
        """Price up (open < close), COT net up → agreement → divergence = 0."""
        bars = [_bar(1910, 1895, 1900, 1910)]  # open=1900, close=1910 → price_dir=+1
        reports = [self._cot(100000), self._cot(110000)]  # cot_dir=+1
        result = _cot_divergence(bars, reports)
        assert result == 0.0

    def test_divergence_bearish_price_bullish_cot(self):
        """Price down (open > close), COT net up → divergence = -1."""
        bars = [_bar(1910, 1895, 1910, 1895)]  # open=1910, close=1895 → price_dir=-1
        reports = [self._cot(100000), self._cot(110000)]  # cot_dir=+1
        result = _cot_divergence(bars, reports)
        assert result == pytest.approx(-1.0)

    def test_insufficient_cot_data(self):
        bars = [_bar(1910, 1895, 1900, 1910)]
        assert _cot_divergence(bars, [self._cot(100000)]) == 0.0

    def test_empty_bars(self):
        assert _cot_divergence([], [self._cot(100000), self._cot(110000)]) == 0.0
