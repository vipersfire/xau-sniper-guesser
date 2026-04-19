"""Tracks and manages open positions — idempotent state."""
import logging
from dataclasses import dataclass
from datetime import datetime
from config.constants import MAX_LOSS_MULTIPLIER

logger = logging.getLogger(__name__)


@dataclass
class OpenPosition:
    trade_id: int
    ticket: int
    symbol: str
    direction: str
    entry_price: float
    sl_price: float
    tp_price: float
    lot_size: float
    open_time: datetime
    expected_sl_loss: float
    regime_type: str
    unrealized_pnl: float = 0.0


class PositionManager:
    def __init__(self):
        self._positions: dict[int, OpenPosition] = {}  # trade_id → position

    def add(self, position: OpenPosition):
        self._positions[position.trade_id] = position

    def remove(self, trade_id: int):
        self._positions.pop(trade_id, None)

    def update_pnl(self, trade_id: int, current_price: float):
        if pos := self._positions.get(trade_id):
            direction_mult = 1 if pos.direction == "buy" else -1
            pnl_pips = (current_price - pos.entry_price) * 100 * direction_mult
            pos.unrealized_pnl = pnl_pips
            # Secondary exit: loss > 2x expected SL
            if pos.unrealized_pnl < -pos.expected_sl_loss * MAX_LOSS_MULTIPLIER:
                logger.warning(
                    "Secondary exit triggered for trade %d: pnl=%.1f < -%.1f",
                    trade_id, pos.unrealized_pnl, pos.expected_sl_loss * MAX_LOSS_MULTIPLIER,
                )
                return True  # signal to close
        return False

    def trail_sl(self, trade_id: int, current_price: float, trail_pips: float = 20.0):
        if pos := self._positions.get(trade_id):
            if pos.direction == "buy":
                new_sl = current_price - trail_pips * 0.01
                if new_sl > pos.sl_price:
                    pos.sl_price = new_sl
            else:
                new_sl = current_price + trail_pips * 0.01
                if new_sl < pos.sl_price:
                    pos.sl_price = new_sl

    def get_all(self) -> list[OpenPosition]:
        return list(self._positions.values())

    def get(self, trade_id: int) -> OpenPosition | None:
        return self._positions.get(trade_id)

    def count(self) -> int:
        return len(self._positions)
