"""Unit tests for anomaly/circuit_breaker.py"""
import pytest
from anomaly.circuit_breaker import BlackSwanCircuitBreaker


class TestBlackSwanCircuitBreaker:
    def setup_method(self):
        self.cb = BlackSwanCircuitBreaker()

    def test_not_tripped_initially(self):
        assert not self.cb.is_tripped()

    def test_reset_clears_trip(self):
        self.cb._trip("test")
        assert self.cb.is_tripped()
        self.cb.reset()
        assert not self.cb.is_tripped()

    # ── spread ────────────────────────────────────────────────────────────

    def test_normal_spread_no_trip(self):
        self.cb.update_spread_baseline(0.3)
        for _ in range(20):
            self.cb.update_spread_baseline(0.3)
        result = self.cb.check_spread(0.5)  # 1.67x — below 3.0 threshold
        assert result is None

    def test_high_spread_trips(self):
        self.cb.update_spread_baseline(0.3)
        for _ in range(20):
            self.cb.update_spread_baseline(0.3)
        result = self.cb.check_spread(1.5)  # 5x — above 3.0 threshold
        assert result is not None
        assert self.cb.is_tripped()

    def test_no_baseline_no_trip(self):
        # No baseline set yet — should not trip
        result = self.cb.check_spread(999.0)
        assert result is None

    # ── price move ────────────────────────────────────────────────────────

    def test_small_price_move_no_trip(self):
        for price in [1900, 1901, 1902, 1903]:
            self.cb.check_price_move(float(price))
        assert not self.cb.is_tripped()

    def test_large_price_move_trips(self):
        # 1.5% move = 28.5 on 1900 → triggers (threshold 1.5%)
        result = None
        self.cb.check_price_move(1900.0)
        result = self.cb.check_price_move(1930.0)  # ~1.58% move
        assert result is not None
        assert self.cb.is_tripped()

    def test_price_move_window_is_30(self):
        # Push 30 prices at 1900, then jump — only last 30 prices matter
        for _ in range(35):
            self.cb.check_price_move(1900.0)
        # At this point the buffer is full of 1900s
        result = self.cb.check_price_move(1930.0)
        assert result is not None  # still trips because oldest is 1900

    # ── volume ────────────────────────────────────────────────────────────

    def test_normal_volume_no_trip(self):
        self.cb.update_volume_baseline(1000)
        for _ in range(20):
            self.cb.update_volume_baseline(1000)
        result = self.cb.check_volume(3000)  # 3x — below 5x threshold
        assert result is None

    def test_extreme_volume_trips(self):
        self.cb.update_volume_baseline(1000)
        for _ in range(20):
            self.cb.update_volume_baseline(1000)
        result = self.cb.check_volume(6000)  # 6x — above 5x threshold
        assert result is not None
        assert self.cb.is_tripped()
