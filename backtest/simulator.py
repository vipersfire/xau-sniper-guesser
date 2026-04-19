"""Trade simulation on historical OHLCV bars."""
import logging
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from config.constants import PIP_SIZE

logger = logging.getLogger(__name__)


@dataclass
class SimTrade:
    entry_time: datetime
    exit_time: datetime | None
    direction: str  # buy | sell
    entry_price: float
    sl_price: float
    tp_price: float
    exit_price: float | None = None
    pnl_pips: float = 0.0
    r_multiple: float = 0.0
    status: str = "pending"
    regime_type: str = ""


def simulate_trades(
    bars: list[dict],
    signals: list[dict],
    sl_pips: float = 40.0,
    tp_pips: float = 120.0,
    max_bars_in_trade: int = 48,
) -> list[SimTrade]:
    """
    Simulate trades on list of OHLCV dicts.
    signals: list of {bar_index, direction, regime_type}
    """
    trades = []
    bars_arr = bars
    n = len(bars_arr)

    for sig in signals:
        idx = sig["bar_index"]
        if idx >= n:
            continue
        entry_bar = bars_arr[idx]
        direction = sig["direction"]
        entry_price = entry_bar["close"]
        regime_type = sig.get("regime_type", "unknown")

        if direction == "buy":
            sl_price = entry_price - sl_pips * PIP_SIZE
            tp_price = entry_price + tp_pips * PIP_SIZE
        else:
            sl_price = entry_price + sl_pips * PIP_SIZE
            tp_price = entry_price - tp_pips * PIP_SIZE

        risk_pips = sl_pips
        trade = SimTrade(
            entry_time=entry_bar["timestamp"],
            exit_time=None,
            direction=direction,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            regime_type=regime_type,
        )

        # Forward-simulate
        for j in range(idx + 1, min(idx + max_bars_in_trade + 1, n)):
            bar = bars_arr[j]
            high, low = bar["high"], bar["low"]

            if direction == "buy":
                if low <= sl_price:
                    trade.exit_price = sl_price
                    trade.pnl_pips = -sl_pips
                    trade.r_multiple = -1.0
                    trade.status = "sl"
                    trade.exit_time = bar["timestamp"]
                    break
                if high >= tp_price:
                    trade.exit_price = tp_price
                    trade.pnl_pips = tp_pips
                    trade.r_multiple = tp_pips / risk_pips
                    trade.status = "tp"
                    trade.exit_time = bar["timestamp"]
                    break
            else:
                if high >= sl_price:
                    trade.exit_price = sl_price
                    trade.pnl_pips = -sl_pips
                    trade.r_multiple = -1.0
                    trade.status = "sl"
                    trade.exit_time = bar["timestamp"]
                    break
                if low <= tp_price:
                    trade.exit_price = tp_price
                    trade.pnl_pips = tp_pips
                    trade.r_multiple = tp_pips / risk_pips
                    trade.status = "tp"
                    trade.exit_time = bar["timestamp"]
                    break

        if trade.status == "pending":
            # Expired — close at last bar close
            last_bar = bars_arr[min(idx + max_bars_in_trade, n - 1)]
            close = last_bar["close"]
            trade.exit_price = close
            pips = (close - entry_price) / PIP_SIZE * (1 if direction == "buy" else -1)
            trade.pnl_pips = pips
            trade.r_multiple = pips / risk_pips
            trade.status = "expired"
            trade.exit_time = last_bar["timestamp"]

        trades.append(trade)

    return trades
