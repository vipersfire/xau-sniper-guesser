"""ICT structural signals: Order Blocks, FVGs, BOS, ChoCH."""
import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OrderBlock:
    price_high: float
    price_low: float
    direction: str  # bullish | bearish
    bar_index: int


@dataclass
class FVG:
    price_high: float
    price_low: float
    direction: str
    bar_index: int


class StructuralSignals:
    """Deterministic ICT concept detectors. No AI."""

    def detect_order_blocks(self, bars: list, lookback: int = 10) -> list[OrderBlock]:
        obs = []
        for i in range(1, min(lookback, len(bars) - 1)):
            bar = bars[-(i + 1)]
            next_bar = bars[-i]
            # Bullish OB: bearish candle followed by strong up move
            if bar["close"] < bar["open"] and next_bar["close"] > bar["high"]:
                obs.append(OrderBlock(
                    price_high=bar["open"],
                    price_low=bar["close"],
                    direction="bullish",
                    bar_index=len(bars) - i - 1,
                ))
            # Bearish OB: bullish candle followed by strong down move
            if bar["close"] > bar["open"] and next_bar["close"] < bar["low"]:
                obs.append(OrderBlock(
                    price_high=bar["close"],
                    price_low=bar["open"],
                    direction="bearish",
                    bar_index=len(bars) - i - 1,
                ))
        return obs

    def detect_fvg(self, bars: list) -> list[FVG]:
        """Fair Value Gap: gap between candle[i-2] high/low and candle[i] low/high."""
        fvgs = []
        for i in range(2, len(bars)):
            a, _, c = bars[i - 2], bars[i - 1], bars[i]
            # Bullish FVG: c.low > a.high
            if c["low"] > a["high"]:
                fvgs.append(FVG(price_high=c["low"], price_low=a["high"], direction="bullish", bar_index=i))
            # Bearish FVG: c.high < a.low
            if c["high"] < a["low"]:
                fvgs.append(FVG(price_high=a["low"], price_low=c["high"], direction="bearish", bar_index=i))
        return fvgs

    def detect_bos(self, bars: list, swing_lookback: int = 5) -> str | None:
        """Break of Structure: price closes beyond recent swing high/low."""
        if len(bars) < swing_lookback + 2:
            return None
        recent = bars[-swing_lookback - 1: -1]
        last = bars[-1]
        swing_high = max(b["high"] for b in recent)
        swing_low = min(b["low"] for b in recent)
        if last["close"] > swing_high:
            return "bullish"
        if last["close"] < swing_low:
            return "bearish"
        return None

    def detect_choch(self, bars: list) -> str | None:
        """Change of Character: last BOS is opposite to previous BOS."""
        if len(bars) < 20:
            return None
        bos_1 = self.detect_bos(bars[-20:-10])
        bos_2 = self.detect_bos(bars[-10:])
        if bos_1 and bos_2 and bos_1 != bos_2:
            return bos_2  # direction of the new character
        return None

    def extract_features(self, bars: list) -> dict:
        if len(bars) < 10:
            return self._empty_features()

        obs = self.detect_order_blocks(bars)
        fvgs = self.detect_fvg(bars[-5:])
        bos = self.detect_bos(bars)
        choch = self.detect_choch(bars)

        current_price = bars[-1]["close"]
        nearest_ob_dist = 0.0
        if obs:
            dists = [abs(current_price - (ob.price_high + ob.price_low) / 2) for ob in obs]
            nearest_ob_dist = min(dists) / current_price * 10000  # in pips

        closes = np.array([b["close"] for b in bars])
        ema50 = _ema(closes, 50)[-1]
        price_vs_ema50 = (current_price - ema50) / ema50 * 100 if ema50 > 0 else 0

        highs = np.array([b["high"] for b in bars])
        lows = np.array([b["low"] for b in bars])
        atr_val = float(np.mean(highs[-14:] - lows[-14:]))

        return {
            "ob_distance_pips": round(nearest_ob_dist, 1),
            "fvg_present": 1.0 if fvgs else 0.0,
            "bos_recent": 1.0 if bos == "bullish" else -1.0 if bos == "bearish" else 0.0,
            "choch_recent": 1.0 if choch == "bullish" else -1.0 if choch == "bearish" else 0.0,
            "price_vs_ema50": round(price_vs_ema50, 4),
            "atr_14_h1": round(atr_val, 4),
        }

    def detect_entry(self, bars: list) -> dict | None:
        """Return entry signal dict if setup is valid."""
        if len(bars) < 20:
            return None
        bos = self.detect_bos(bars)
        obs = self.detect_order_blocks(bars)
        if not bos or not obs:
            return None
        bullish_obs = [ob for ob in obs if ob.direction == "bullish"]
        bearish_obs = [ob for ob in obs if ob.direction == "bearish"]
        current_price = bars[-1]["close"]
        if bos == "bullish" and bullish_obs:
            ob = bullish_obs[0]
            if ob.price_low <= current_price <= ob.price_high * 1.002:
                return {"direction": "buy", "regime_type": "trending_bullish"}
        if bos == "bearish" and bearish_obs:
            ob = bearish_obs[0]
            if ob.price_low * 0.998 <= current_price <= ob.price_high:
                return {"direction": "sell", "regime_type": "trending_bearish"}
        return None

    def _empty_features(self) -> dict:
        return {
            "ob_distance_pips": 0.0, "fvg_present": 0.0,
            "bos_recent": 0.0, "choch_recent": 0.0,
            "price_vs_ema50": 0.0, "atr_14_h1": 0.0,
        }


def _ema(values: np.ndarray, period: int) -> np.ndarray:
    result = np.zeros_like(values, dtype=float)
    k = 2.0 / (period + 1)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = values[i] * k + result[i - 1] * (1 - k)
    return result
