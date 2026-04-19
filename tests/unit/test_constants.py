"""Unit tests for config/constants.py"""
import pytest
from config.constants import (
    SYMBOL, TIMEFRAMES, TIMEFRAME_SECONDS, SESSION_WINDOWS,
    EventLevel, EVENT_LEVEL_SIZE_FACTOR,
    MAX_KELLY_FRACTION, DEFAULT_CONFIDENCE_THRESHOLD,
    PSI_WATCH, PSI_INVESTIGATE, PSI_CRITICAL,
)


class TestConstants:
    def test_symbol(self):
        assert SYMBOL == "XAUUSD"

    def test_timeframes_order(self):
        # Should be in decreasing order (D1 first, M15 last)
        assert TIMEFRAMES.index("D1") < TIMEFRAMES.index("H4")
        assert TIMEFRAMES.index("H4") < TIMEFRAMES.index("H1")
        assert TIMEFRAMES.index("H1") < TIMEFRAMES.index("M15")

    def test_timeframe_seconds_consistent(self):
        assert TIMEFRAME_SECONDS["M15"] == 900
        assert TIMEFRAME_SECONDS["H1"] == 3600
        assert TIMEFRAME_SECONDS["H4"] == 14400
        assert TIMEFRAME_SECONDS["D1"] == 86400

    def test_session_windows_coverage(self):
        assert "asian" in SESSION_WINDOWS
        assert "london" in SESSION_WINDOWS
        assert "ny" in SESSION_WINDOWS
        assert "overlap" in SESSION_WINDOWS

    def test_psi_thresholds_ordered(self):
        assert PSI_WATCH < PSI_INVESTIGATE < PSI_CRITICAL

    def test_confidence_threshold_range(self):
        assert 0.0 < DEFAULT_CONFIDENCE_THRESHOLD < 1.0

    def test_kelly_fraction_cap(self):
        assert 0.0 < MAX_KELLY_FRACTION <= 0.05  # never bet more than 5%


class TestEventLevel:
    def test_unknown_zero_size(self):
        assert EVENT_LEVEL_SIZE_FACTOR[EventLevel.UNKNOWN] == 0.0

    def test_known_known_full_size(self):
        assert EVENT_LEVEL_SIZE_FACTOR[EventLevel.KNOWN_KNOWN] == 1.0

    def test_size_factors_decrease_with_uncertainty(self):
        factors = [
            EVENT_LEVEL_SIZE_FACTOR[EventLevel.KNOWN_KNOWN],
            EVENT_LEVEL_SIZE_FACTOR[EventLevel.KNOWN_UNUSUAL],
            EVENT_LEVEL_SIZE_FACTOR[EventLevel.KNOWN_VARIANT],
            EVENT_LEVEL_SIZE_FACTOR[EventLevel.UNKNOWN],
        ]
        assert factors == sorted(factors, reverse=True)
