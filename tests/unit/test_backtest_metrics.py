"""Unit tests for backtest/metrics.py"""
import pytest
from backtest.metrics import compute_metrics


class TestComputeMetrics:
    def _trades(self, pnls: list[float]) -> list[dict]:
        return [{"pnl": p, "r_multiple": p / 40} for p in pnls]

    def test_empty_trades(self):
        result = compute_metrics([])
        assert "error" in result

    def test_all_wins(self):
        trades = self._trades([100, 80, 120, 90])
        m = compute_metrics(trades)
        assert m["win_rate"] == pytest.approx(1.0)
        assert m["total_pnl"] == pytest.approx(390.0)
        assert m["profit_factor"] == float("inf")

    def test_all_losses(self):
        trades = self._trades([-40, -40, -40])
        m = compute_metrics(trades)
        assert m["win_rate"] == pytest.approx(0.0)
        assert m["total_pnl"] == pytest.approx(-120.0)

    def test_mixed_trades(self):
        trades = self._trades([120, -40, 120, -40, 120])
        m = compute_metrics(trades)
        assert m["win_rate"] == pytest.approx(0.6)
        assert m["total_trades"] == 5
        assert m["total_pnl"] == pytest.approx(280.0)  # 120-40+120-40+120=280
        assert m["profit_factor"] > 1.0

    def test_profit_factor(self):
        trades = self._trades([120, 120, -40, -40])
        m = compute_metrics(trades)
        assert m["profit_factor"] == pytest.approx(3.0)

    def test_max_drawdown_negative(self):
        trades = self._trades([100, -200, 50])
        m = compute_metrics(trades)
        assert m["max_drawdown"] < 0

    def test_sharpe_zero_for_constant_returns(self):
        trades = self._trades([0, 0, 0, 0, 0])
        m = compute_metrics(trades)
        assert m["sharpe"] == 0.0

    def test_expectancy_positive_edge(self):
        trades = self._trades([120, 120, 120, -40, -40])
        m = compute_metrics(trades)
        assert m["expectancy"] > 0

    def test_avg_r(self):
        # R multiples: 120/40=3R, -40/40=-1R
        trades = self._trades([120, -40])
        m = compute_metrics(trades)
        assert m["avg_r"] == pytest.approx(1.0)
