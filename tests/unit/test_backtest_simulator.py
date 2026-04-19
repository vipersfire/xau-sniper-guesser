"""Unit tests for backtest/simulator.py"""
from datetime import datetime, timezone
import pytest
from backtest.simulator import simulate_trades, SimTrade


def _bar(price: float, i: int) -> dict:
    from datetime import timedelta
    return {
        "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
        "open":  price,
        "high":  price + 0.05,  # tight range so SL/TP not accidentally triggered
        "low":   price - 0.05,
        "close": price,
        "volume": 1000,
    }


def _bars(n: int, base: float = 1900.0) -> list[dict]:
    return [_bar(base, i) for i in range(n)]


class TestSimulateTrades:
    def test_no_signals_no_trades(self):
        bars = _bars(100)
        trades = simulate_trades(bars, signals=[])
        assert trades == []

    def test_tp_hit_long(self):
        bars = _bars(50, base=1900)
        # Override bar 20 to have high > tp_price (1900 + 120*0.01 = 1901.2)
        tp_price = 1900 + 120 * 0.01
        for i in range(20, 50):
            bars[i]["high"] = tp_price + 1

        signals = [{"bar_index": 10, "direction": "buy", "regime_type": "trending_bullish"}]
        trades = simulate_trades(bars, signals, sl_pips=40, tp_pips=120)
        assert len(trades) == 1
        assert trades[0].status == "tp"
        assert trades[0].pnl_pips == pytest.approx(120.0)
        assert trades[0].r_multiple == pytest.approx(3.0)

    def test_sl_hit_long(self):
        bars = _bars(50, base=1900)
        sl_price = 1900 - 40 * 0.01
        for i in range(15, 50):
            bars[i]["low"] = sl_price - 1

        signals = [{"bar_index": 10, "direction": "buy", "regime_type": "ranging"}]
        trades = simulate_trades(bars, signals, sl_pips=40, tp_pips=120)
        assert len(trades) == 1
        assert trades[0].status == "sl"
        assert trades[0].pnl_pips == pytest.approx(-40.0)
        assert trades[0].r_multiple == pytest.approx(-1.0)

    def test_tp_hit_short(self):
        bars = _bars(50, base=1900)
        tp_price = 1900 - 120 * 0.01
        for i in range(20, 50):
            bars[i]["low"] = tp_price - 1

        signals = [{"bar_index": 10, "direction": "sell", "regime_type": "trending_bearish"}]
        trades = simulate_trades(bars, signals, sl_pips=40, tp_pips=120)
        assert len(trades) == 1
        assert trades[0].status == "tp"
        assert trades[0].pnl_pips == pytest.approx(120.0)

    def test_expired_trade(self):
        # TP and SL never hit — expires after max_bars
        bars = _bars(100)
        signals = [{"bar_index": 0, "direction": "buy", "regime_type": "unknown"}]
        trades = simulate_trades(bars, signals, sl_pips=40, tp_pips=120, max_bars_in_trade=10)
        assert len(trades) == 1
        assert trades[0].status == "expired"

    def test_signal_beyond_bars(self):
        bars = _bars(5)
        signals = [{"bar_index": 99, "direction": "buy", "regime_type": "test"}]
        trades = simulate_trades(bars, signals)
        assert trades == []

    def test_multiple_signals(self):
        bars = _bars(100)
        signals = [
            {"bar_index": 5,  "direction": "buy",  "regime_type": "a"},
            {"bar_index": 50, "direction": "sell", "regime_type": "b"},
        ]
        trades = simulate_trades(bars, signals, sl_pips=40, tp_pips=120, max_bars_in_trade=10)
        assert len(trades) == 2
        assert {t.direction for t in trades} == {"buy", "sell"}

    def test_regime_type_carried(self):
        bars = _bars(50)
        signals = [{"bar_index": 5, "direction": "buy", "regime_type": "trending_bullish"}]
        trades = simulate_trades(bars, signals)
        assert trades[0].regime_type == "trending_bullish"
