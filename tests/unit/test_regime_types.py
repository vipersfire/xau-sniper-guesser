"""Unit tests for engine/regime/regime_types.py"""
import pytest
from engine.regime.regime_types import (
    RegimeType, RegimeStats, RegimeResult, DEFAULT_REGIME_STATS,
)
from datetime import datetime


class TestRegimeType:
    def test_all_values_are_strings(self):
        for rt in RegimeType:
            assert isinstance(rt.value, str)

    def test_unknown_exists(self):
        assert RegimeType.UNKNOWN.value == "unknown"

    def test_lookup_by_value(self):
        rt = RegimeType("trending_bullish")
        assert rt == RegimeType.TRENDING_BULLISH


class TestRegimeStats:
    def _make_stats(self, **kwargs) -> RegimeStats:
        defaults = dict(
            regime_type=RegimeType.TRENDING_BULLISH,
            occurrences=20,
            avg_move_pips=180,
            avg_duration_hours=5.0,
            win_rate=0.68,
            avg_max_drawdown_pips=35,
            suggested_sl_pips=40,
            suggested_tp_pips=160,
            confidence_threshold=0.65,
            sample_quality="High",
        )
        defaults.update(kwargs)
        return RegimeStats(**defaults)

    def test_rr_ratio(self):
        stats = self._make_stats(suggested_sl_pips=40, suggested_tp_pips=160)
        assert stats.rr_ratio == pytest.approx(4.0)

    def test_rr_ratio_zero_sl(self):
        stats = self._make_stats(suggested_sl_pips=0)
        assert stats.rr_ratio == 0.0

    def test_tradeable_enough_occurrences(self):
        stats = self._make_stats(occurrences=10, win_rate=0.55, sample_quality="High")
        assert stats.is_tradeable

    def test_not_tradeable_too_few_occurrences(self):
        stats = self._make_stats(occurrences=5, win_rate=0.70)
        assert not stats.is_tradeable

    def test_not_tradeable_low_win_rate(self):
        stats = self._make_stats(occurrences=20, win_rate=0.45)
        assert not stats.is_tradeable

    def test_not_tradeable_low_sample_quality(self):
        stats = self._make_stats(occurrences=20, win_rate=0.65, sample_quality="Low")
        assert not stats.is_tradeable


class TestDefaultRegimeStats:
    def test_all_regimes_have_stats(self):
        for rt in RegimeType:
            assert rt in DEFAULT_REGIME_STATS, f"Missing stats for {rt}"

    def test_unknown_regime_not_tradeable(self):
        stats = DEFAULT_REGIME_STATS[RegimeType.UNKNOWN]
        assert not stats.is_tradeable

    def test_trending_bullish_tradeable(self):
        stats = DEFAULT_REGIME_STATS[RegimeType.TRENDING_BULLISH]
        assert stats.is_tradeable

    def test_confidence_thresholds_valid(self):
        for rt, stats in DEFAULT_REGIME_STATS.items():
            assert 0.0 <= stats.confidence_threshold <= 1.0, f"{rt} has invalid threshold"


class TestRegimeResult:
    def test_defaults(self):
        result = RegimeResult(
            regime_type=RegimeType.TRENDING_BULLISH,
            confidence=0.75,
            stats=None,
        )
        assert not result.should_abstain
        assert isinstance(result.classified_at, datetime)
        assert result.feature_snapshot == {}

    def test_abstain_flag(self):
        result = RegimeResult(
            regime_type=RegimeType.UNKNOWN,
            confidence=0.0,
            stats=None,
            should_abstain=True,
            abstain_reason="confidence too low",
        )
        assert result.should_abstain
        assert "confidence" in result.abstain_reason
