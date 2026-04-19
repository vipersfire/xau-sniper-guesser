"""Unit tests for utils/data_quality.py"""
import pytest
from utils.data_quality import DataQualityFlag, OHLCVQuality, score_bar


class TestOHLCVQuality:
    def test_default_is_high_quality(self):
        q = OHLCVQuality()
        assert q.is_high_quality
        assert q.is_usable

    def test_penalize_reduces_score(self):
        q = OHLCVQuality()
        q.penalize(DataQualityFlag.HIGH_SPREAD, 0.1)
        assert q.quality_score == pytest.approx(0.9)
        assert DataQualityFlag.HIGH_SPREAD in q.flags

    def test_multiple_penalties(self):
        q = OHLCVQuality()
        q.penalize(DataQualityFlag.INTERPOLATED, 0.5)
        q.penalize(DataQualityFlag.GAP_ADJACENT, 0.15)
        assert q.quality_score == pytest.approx(0.35)
        assert not q.is_usable

    def test_score_floor_at_zero(self):
        q = OHLCVQuality()
        q.penalize(DataQualityFlag.INTERPOLATED, 0.5)
        q.penalize(DataQualityFlag.INTERPOLATED, 0.5)
        q.penalize(DataQualityFlag.INTERPOLATED, 0.5)
        assert q.quality_score >= 0.0

    def test_not_high_quality_with_flags(self):
        q = OHLCVQuality()
        q.penalize(DataQualityFlag.NEWS_ADJACENT, 0.05)
        assert not q.is_high_quality
        assert q.is_usable  # only slightly penalized


class TestScoreBar:
    def _make_bar(self, o=1900, h=1910, l=1895, c=1905):
        return o, h, l, c

    def test_valid_bar_is_high_quality(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=1000, spread=0.3,
        )
        assert q.is_usable
        assert not q.flags  # no flags on clean bar

    def test_invalid_ohlcv_flagged(self):
        # high < low — structurally invalid
        q = score_bar(
            open_=1900, high=1890, low=1895, close=1905,
            volume=1000, spread=0.3,
        )
        assert DataQualityFlag.INTERPOLATED in q.flags
        assert q.quality_score < 1.0

    def test_high_spread_flagged(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=1000, spread=10.0, avg_spread=1.0,
        )
        assert DataQualityFlag.HIGH_SPREAD in q.flags

    def test_low_volume_flagged(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=5, spread=0.3, avg_volume=1000,
        )
        assert DataQualityFlag.LOW_VOLUME in q.flags

    def test_gap_adjacent_flagged(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=1000, spread=0.3, prev_close=1850,  # >5% gap
        )
        assert DataQualityFlag.GAP_ADJACENT in q.flags

    def test_news_adjacent_flagged(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=1000, spread=0.3, is_news_adjacent=True,
        )
        assert DataQualityFlag.NEWS_ADJACENT in q.flags

    def test_weekend_edge_flagged(self):
        q = score_bar(
            open_=1900, high=1910, low=1895, close=1905,
            volume=1000, spread=0.3, is_weekend_edge=True,
        )
        assert DataQualityFlag.WEEKEND_EDGE in q.flags
