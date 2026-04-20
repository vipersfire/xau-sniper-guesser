"""Retail trap signal — detects liquidity sweeps followed by strong rejections.

A retail trap occurs when price briefly breaks a recent high/low (sweeping stops),
then reverses sharply — trapping breakout traders on the wrong side.
"""
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Minimum rejection size as fraction of sweep candle's range
MIN_REJECTION_RATIO = 0.6
# Lookback window for finding the swept level
SWEEP_LOOKBACK = 20


@dataclass
class RetailTrapSignal:
    direction: str          # "bull_trap" (swept high, rejected down) | "bear_trap" (swept low, rejected up)
    swept_level: float      # price level that was swept
    rejection_strength: float  # [0, 1] — how strong the wick rejection was
    bar_index: int


def detect_retail_traps(bars: list[dict]) -> list[RetailTrapSignal]:
    """Scan bars and return all detected retail trap signals.

    A bull trap: bar sweeps the N-bar high then closes below it with a large upper wick.
    A bear trap: bar sweeps the N-bar low then closes above it with a large lower wick.
    """
    signals: list[RetailTrapSignal] = []
    if len(bars) < SWEEP_LOOKBACK + 1:
        return signals

    for i in range(SWEEP_LOOKBACK, len(bars)):
        bar = bars[i]
        lookback = bars[i - SWEEP_LOOKBACK: i]

        high = bar["high"]
        low = bar["low"]
        close = bar["close"]
        bar_range = high - low
        if bar_range == 0:
            continue

        prev_high = max(b["high"] for b in lookback)
        prev_low = min(b["low"] for b in lookback)

        # Bull trap: sweep of prev_high + close below it + large upper wick
        if high > prev_high and close < prev_high:
            upper_wick = high - max(bar["open"], close)
            rejection = upper_wick / bar_range
            if rejection >= MIN_REJECTION_RATIO:
                signals.append(RetailTrapSignal(
                    direction="bull_trap",
                    swept_level=prev_high,
                    rejection_strength=round(rejection, 3),
                    bar_index=i,
                ))

        # Bear trap: sweep of prev_low + close above it + large lower wick
        elif low < prev_low and close > prev_low:
            lower_wick = min(bar["open"], close) - low
            rejection = lower_wick / bar_range
            if rejection >= MIN_REJECTION_RATIO:
                signals.append(RetailTrapSignal(
                    direction="bear_trap",
                    swept_level=prev_low,
                    rejection_strength=round(rejection, 3),
                    bar_index=i,
                ))

    return signals


def latest_trap_score(bars: list[dict], lookback: int = 5) -> float:
    """Score [0, 1] based on most recent trap in the last `lookback` bars."""
    if not bars:
        return 0.0
    traps = detect_retail_traps(bars)
    if not traps:
        return 0.0
    last_bar_idx = len(bars) - 1
    recent = [t for t in traps if last_bar_idx - t.bar_index <= lookback]
    if not recent:
        return 0.0
    return max(t.rejection_strength for t in recent)
