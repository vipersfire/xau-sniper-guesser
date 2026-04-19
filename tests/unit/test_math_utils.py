"""Unit tests for utils/math_utils.py"""
import numpy as np
import pytest
from utils.math_utils import (
    kelly_fraction,
    anomaly_adjusted_size,
    r_multiple,
    atr,
    psi,
    ema,
    zscore,
)


class TestKellyFraction:
    def test_positive_edge(self):
        # 60% win rate, 1.5R reward → positive Kelly
        k = kelly_fraction(win_rate=0.60, avg_win=150, avg_loss=100)
        assert k > 0

    def test_zero_edge(self):
        # 50% win rate, 1:1 R → Kelly ≈ 0
        k = kelly_fraction(win_rate=0.50, avg_win=100, avg_loss=100)
        assert abs(k) < 0.01

    def test_zero_win_rate(self):
        assert kelly_fraction(0.0, 100, 100) == 0.0

    def test_zero_avg_loss(self):
        assert kelly_fraction(0.6, 100, 0) == 0.0

    def test_negative_edge(self):
        # 40% win rate, 1:1 R → negative Kelly (don't bet)
        k = kelly_fraction(win_rate=0.40, avg_win=100, avg_loss=100)
        assert k < 0


class TestAnomalyAdjustedSize:
    def test_zero_anomaly_full_size(self):
        assert anomaly_adjusted_size(1.0, 0.0) == pytest.approx(1.0)

    def test_max_anomaly_zero_size(self):
        assert anomaly_adjusted_size(1.0, 1.0) == pytest.approx(0.0)

    def test_mid_anomaly(self):
        # score=0.3 → (0.7)^3 ≈ 0.343
        result = anomaly_adjusted_size(1.0, 0.3)
        assert result == pytest.approx(0.343, abs=0.001)

    def test_score_clamp_above_one(self):
        # scores above 1 should be clamped to 1 → size = 0
        assert anomaly_adjusted_size(1.0, 1.5) == pytest.approx(0.0)

    def test_score_clamp_below_zero(self):
        # scores below 0 should be clamped to 0 → size unchanged
        assert anomaly_adjusted_size(1.0, -0.5) == pytest.approx(1.0)

    def test_base_size_scaling(self):
        result = anomaly_adjusted_size(2.0, 0.0)
        assert result == pytest.approx(2.0)


class TestRMultiple:
    def test_long_tp_hit(self):
        r = r_multiple(entry=1900, exit_=1940, sl=1880, direction=1)
        assert r == pytest.approx(2.0)

    def test_long_sl_hit(self):
        r = r_multiple(entry=1900, exit_=1880, sl=1880, direction=1)
        assert r == pytest.approx(-1.0)

    def test_short_tp_hit(self):
        r = r_multiple(entry=1900, exit_=1860, sl=1920, direction=-1)
        assert r == pytest.approx(2.0)

    def test_zero_risk(self):
        # SL == entry → avoid division by zero
        r = r_multiple(entry=1900, exit_=1940, sl=1900, direction=1)
        assert r == 0.0


class TestATR:
    def test_basic_shape(self):
        n = 30
        highs = np.random.uniform(1910, 1920, n)
        lows = highs - np.random.uniform(5, 15, n)
        closes = (highs + lows) / 2
        result = atr(highs, lows, closes, period=14)
        assert result.shape == (n,)

    def test_all_positive(self):
        highs = np.array([100.0, 105.0, 103.0, 107.0, 104.0] * 5)
        lows = highs - 5
        closes = (highs + lows) / 2
        result = atr(highs, lows, closes, period=5)
        assert np.all(result >= 0)

    def test_stable_range(self):
        # Constant candle size → ATR should converge to that size
        highs = np.full(50, 10.0)
        lows = np.full(50, 0.0)
        closes = np.full(50, 5.0)
        result = atr(highs, lows, closes, period=14)
        assert result[-1] == pytest.approx(10.0, abs=0.1)


class TestPSI:
    def test_identical_distributions(self):
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 1000)
        result = psi(data, data)
        assert result < 0.01

    def test_different_distributions(self):
        rng = np.random.default_rng(42)
        expected = rng.normal(0, 1, 1000)
        actual = rng.normal(5, 1, 1000)  # shifted mean
        result = psi(expected, actual)
        assert result > 0.25  # critical drift

    def test_nonnegative(self):
        rng = np.random.default_rng(0)
        a = rng.uniform(0, 1, 500)
        b = rng.uniform(0.1, 1.1, 500)
        assert psi(a, b) >= 0


class TestEMA:
    def test_single_value(self):
        result = ema(np.array([5.0]), period=3)
        assert result[0] == pytest.approx(5.0)

    def test_smoothing(self):
        values = np.array([10.0, 10.0, 10.0, 20.0, 20.0, 20.0])
        result = ema(values, period=3)
        # EMA should be between old and new value after jump
        assert 10.0 < result[-1] < 20.0

    def test_constant_series(self):
        values = np.full(20, 42.0)
        result = ema(values, period=5)
        assert np.allclose(result, 42.0)


class TestZScore:
    def test_zero_mean_unit_std(self):
        rng = np.random.default_rng(1)
        values = rng.normal(100, 10, 200)
        result = zscore(values, window=20)
        valid = result[~np.isnan(result)]
        assert abs(valid.mean()) < 0.5

    def test_nan_before_window(self):
        values = np.arange(30, dtype=float)
        result = zscore(values, window=10)
        assert np.all(np.isnan(result[:9]))
        assert not np.isnan(result[9])
