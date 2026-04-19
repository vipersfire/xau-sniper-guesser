"""Unit tests for engine/trading/position_manager.py"""
from datetime import datetime, timezone
import pytest
from engine.trading.position_manager import PositionManager, OpenPosition


def _pos(trade_id: int = 1, direction: str = "buy", entry: float = 1900.0, sl: float = 1880.0, tp: float = 1940.0) -> OpenPosition:
    return OpenPosition(
        trade_id=trade_id,
        ticket=trade_id * 1000,
        symbol="XAUUSD",
        direction=direction,
        entry_price=entry,
        sl_price=sl,
        tp_price=tp,
        lot_size=0.1,
        open_time=datetime.now(timezone.utc),
        expected_sl_loss=20.0,  # 20 pips
        regime_type="trending_bullish",
    )


class TestPositionManager:
    def test_add_and_get(self):
        pm = PositionManager()
        pos = _pos(1)
        pm.add(pos)
        assert pm.get(1) is pos

    def test_remove(self):
        pm = PositionManager()
        pm.add(_pos(1))
        pm.remove(1)
        assert pm.get(1) is None

    def test_count(self):
        pm = PositionManager()
        pm.add(_pos(1))
        pm.add(_pos(2))
        assert pm.count() == 2

    def test_get_all(self):
        pm = PositionManager()
        pm.add(_pos(1))
        pm.add(_pos(2))
        assert len(pm.get_all()) == 2

    def test_get_nonexistent_returns_none(self):
        pm = PositionManager()
        assert pm.get(999) is None

    def test_remove_nonexistent_no_error(self):
        pm = PositionManager()
        pm.remove(999)  # Should not raise

    # ── update_pnl ────────────────────────────────────────────────────────

    def test_update_pnl_long_profitable(self):
        pm = PositionManager()
        pm.add(_pos(1, direction="buy", entry=1900))
        needs_exit = pm.update_pnl(1, current_price=1910)
        assert not needs_exit
        assert pm.get(1).unrealized_pnl > 0

    def test_update_pnl_long_secondary_exit(self):
        pm = PositionManager()
        # expected_sl_loss=20 pips, MAX_LOSS_MULTIPLIER=2 → exit if loss > 40 pips
        pm.add(_pos(1, direction="buy", entry=1900, sl=1880))
        # Drop 50 pips → triggers secondary exit (50 > 40)
        needs_exit = pm.update_pnl(1, current_price=1849)
        assert needs_exit

    def test_update_pnl_short_profitable(self):
        pm = PositionManager()
        pm.add(_pos(1, direction="sell", entry=1900, sl=1920, tp=1860))
        needs_exit = pm.update_pnl(1, current_price=1885)
        assert not needs_exit
        assert pm.get(1).unrealized_pnl > 0

    # ── trail_sl ─────────────────────────────────────────────────────────

    def test_trail_sl_long_moves_up(self):
        pm = PositionManager()
        pm.add(_pos(1, direction="buy", entry=1900, sl=1880))
        pm.trail_sl(1, current_price=1930, trail_pips=20)
        # New SL = 1930 - 20*0.01 = 1929.8 ... wait, trail_pips=20 means 20 pips = 20*0.01=0.2
        new_sl = pm.get(1).sl_price
        assert new_sl > 1880  # SL moved up

    def test_trail_sl_long_does_not_move_down(self):
        pm = PositionManager()
        # SL already trailed up to 1895; price pulls back to 1870.
        # new candidate SL = 1870 - 20*0.01 = 1869.8 < 1895 → should NOT move.
        pm.add(_pos(1, direction="buy", entry=1900, sl=1895))
        pm.trail_sl(1, current_price=1870, trail_pips=20)
        assert pm.get(1).sl_price == 1895

    def test_trail_sl_short_moves_down(self):
        pm = PositionManager()
        pm.add(_pos(1, direction="sell", entry=1900, sl=1920))
        pm.trail_sl(1, current_price=1870, trail_pips=20)
        new_sl = pm.get(1).sl_price
        assert new_sl < 1920  # SL moved down (toward price)
