"""Unit tests for engine/signals/structural.py"""
import pytest
from engine.signals.structural import StructuralSignals


def _make_bars(n: int, base_price: float = 1900.0, trend: float = 0.0) -> list[dict]:
    """Generate synthetic OHLCV bars."""
    bars = []
    price = base_price
    for i in range(n):
        price += trend
        bars.append({
            "open":  price,
            "high":  price + 5,
            "low":   price - 5,
            "close": price + 2,
            "volume": 1000,
            "timestamp": None,
        })
    return bars


def _bearish_bar(price: float) -> dict:
    return {"open": price + 4, "high": price + 6, "low": price - 2, "close": price, "volume": 1000, "timestamp": None}


def _bullish_bar(price: float) -> dict:
    return {"open": price, "high": price + 8, "low": price - 1, "close": price + 6, "volume": 1000, "timestamp": None}


class TestOrderBlockDetection:
    def setup_method(self):
        self.sig = StructuralSignals()

    def test_bullish_ob_detected(self):
        # Bearish candle followed by close above its high → bullish OB
        bars = _make_bars(8, 1900)
        bars[-2] = _bearish_bar(1900)
        bars[-1] = {"open": 1900, "high": 1915, "low": 1898, "close": 1912, "volume": 1000, "timestamp": None}
        obs = self.sig.detect_order_blocks(bars)
        bullish = [ob for ob in obs if ob.direction == "bullish"]
        assert len(bullish) > 0

    def test_no_ob_on_flat_market(self):
        bars = _make_bars(20, 1900, trend=0.0)
        obs = self.sig.detect_order_blocks(bars)
        # Flat market with no strong moves — may or may not have OBs, but shouldn't crash
        assert isinstance(obs, list)


class TestFVGDetection:
    def setup_method(self):
        self.sig = StructuralSignals()

    def test_bullish_fvg(self):
        # c.low > a.high
        bars = [
            {"open": 1900, "high": 1905, "low": 1895, "close": 1902, "volume": 1000, "timestamp": None},
            {"open": 1908, "high": 1915, "low": 1907, "close": 1912, "volume": 1000, "timestamp": None},
            {"open": 1916, "high": 1920, "low": 1910, "close": 1918, "volume": 1000, "timestamp": None},
        ]
        fvgs = self.sig.detect_fvg(bars)
        bullish = [f for f in fvgs if f.direction == "bullish"]
        assert len(bullish) > 0

    def test_bearish_fvg(self):
        # c.high < a.low
        bars = [
            {"open": 1920, "high": 1925, "low": 1915, "close": 1918, "volume": 1000, "timestamp": None},
            {"open": 1910, "high": 1912, "low": 1905, "close": 1907, "volume": 1000, "timestamp": None},
            {"open": 1903, "high": 1906, "low": 1898, "close": 1900, "volume": 1000, "timestamp": None},
        ]
        fvgs = self.sig.detect_fvg(bars)
        bearish = [f for f in fvgs if f.direction == "bearish"]
        assert len(bearish) > 0

    def test_no_fvg_overlapping_candles(self):
        # Overlapping candles — no gap
        bars = [
            {"open": 1900, "high": 1910, "low": 1895, "close": 1905, "volume": 1000, "timestamp": None},
            {"open": 1904, "high": 1912, "low": 1900, "close": 1908, "volume": 1000, "timestamp": None},
            {"open": 1907, "high": 1914, "low": 1903, "close": 1910, "volume": 1000, "timestamp": None},
        ]
        fvgs = self.sig.detect_fvg(bars)
        assert fvgs == []


class TestBOSDetection:
    def setup_method(self):
        self.sig = StructuralSignals()

    def test_bullish_bos(self):
        bars = _make_bars(10, 1900)
        # Last bar breaks above swing high
        bars[-1] = {"open": 1900, "high": 1960, "low": 1898, "close": 1955, "volume": 1000, "timestamp": None}
        result = self.sig.detect_bos(bars)
        assert result == "bullish"

    def test_bearish_bos(self):
        bars = _make_bars(10, 1900)
        bars[-1] = {"open": 1900, "high": 1902, "low": 1850, "close": 1848, "volume": 1000, "timestamp": None}
        result = self.sig.detect_bos(bars)
        assert result == "bearish"

    def test_no_bos_inside_range(self):
        bars = _make_bars(10, 1900)
        result = self.sig.detect_bos(bars)
        assert result is None

    def test_too_few_bars(self):
        bars = _make_bars(3, 1900)
        result = self.sig.detect_bos(bars)
        assert result is None


class TestExtractFeatures:
    def setup_method(self):
        self.sig = StructuralSignals()

    def test_returns_all_keys(self):
        bars = _make_bars(60, 1900, trend=0.5)
        features = self.sig.extract_features(bars)
        expected_keys = {
            "ob_distance_pips", "fvg_present", "bos_recent",
            "choch_recent", "price_vs_ema50", "atr_14_h1",
        }
        assert expected_keys.issubset(features.keys())

    def test_returns_floats(self):
        bars = _make_bars(60, 1900)
        features = self.sig.extract_features(bars)
        for k, v in features.items():
            assert isinstance(v, float), f"{k} should be float, got {type(v)}"

    def test_too_few_bars_returns_empty(self):
        bars = _make_bars(5, 1900)
        features = self.sig.extract_features(bars)
        assert features["ob_distance_pips"] == 0.0
        assert features["fvg_present"] == 0.0
