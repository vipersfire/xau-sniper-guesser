"""Unit tests for utils/time_utils.py"""
from datetime import datetime, timezone
import pytest
from utils.time_utils import current_session, is_market_open, bar_open_time, seconds_until_bar_close


class TestCurrentSession:
    def _dt(self, hour: int) -> datetime:
        return datetime(2024, 3, 6, hour, 0, 0, tzinfo=timezone.utc)  # Wednesday

    def test_asian_session(self):
        assert current_session(self._dt(3)) == "asian"

    def test_london_session(self):
        # 8 UTC — London only (not overlap, not NY yet)
        assert current_session(self._dt(8)) == "london"

    def test_ny_session(self):
        assert current_session(self._dt(16)) == "ny"

    def test_overlap_session(self):
        # 13 UTC — London + NY both open
        assert current_session(self._dt(13)) == "overlap"

    def test_off_hours(self):
        # 23 UTC — no session
        assert current_session(self._dt(23)) == "off_hours"


class TestIsMarketOpen:
    def _dt(self, weekday: int, hour: int = 12) -> datetime:
        # Monday=0, Sunday=6
        days_from_mon = weekday
        base = datetime(2024, 3, 4, hour, 0, 0, tzinfo=timezone.utc)  # Monday
        from datetime import timedelta
        return base + timedelta(days=days_from_mon)

    def test_monday_open(self):
        assert is_market_open(self._dt(0)) is True

    def test_wednesday_open(self):
        assert is_market_open(self._dt(2)) is True

    def test_saturday_closed(self):
        assert is_market_open(self._dt(5)) is False

    def test_friday_before_close(self):
        assert is_market_open(self._dt(4, hour=20)) is True

    def test_friday_after_close(self):
        assert is_market_open(self._dt(4, hour=21)) is False


class TestBarOpenTime:
    def test_h1_alignment(self):
        dt = datetime(2024, 3, 6, 14, 37, 22, tzinfo=timezone.utc)
        bar = bar_open_time(dt, timeframe_seconds=3600)
        assert bar.hour == 14
        assert bar.minute == 0
        assert bar.second == 0

    def test_m15_alignment(self):
        dt = datetime(2024, 3, 6, 14, 22, 0, tzinfo=timezone.utc)
        bar = bar_open_time(dt, timeframe_seconds=900)
        assert bar.hour == 14
        assert bar.minute == 15

    def test_d1_alignment(self):
        dt = datetime(2024, 3, 6, 18, 45, 0, tzinfo=timezone.utc)
        bar = bar_open_time(dt, timeframe_seconds=86400)
        assert bar.hour == 0
        assert bar.minute == 0


class TestSecondsUntilBarClose:
    def test_returns_positive(self):
        dt = datetime(2024, 3, 6, 14, 30, 0, tzinfo=timezone.utc)
        remaining = seconds_until_bar_close(dt, timeframe_seconds=3600)
        assert remaining > 0

    def test_less_than_period(self):
        dt = datetime(2024, 3, 6, 14, 30, 0, tzinfo=timezone.utc)
        remaining = seconds_until_bar_close(dt, timeframe_seconds=3600)
        assert remaining <= 3600
