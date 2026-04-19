"""Black Swan Circuit Breaker — completely bypasses ML, fires on pure rules."""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from config.constants import (
    CB_GOLD_30MIN_MOVE_PCT,
    CB_SPREAD_VS_BASELINE,
    CB_VIX_SPIKE_1HR,
    CB_VOLUME_VS_BASELINE,
)

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerTrip:
    reason: str
    triggered_at: datetime
    severity: str  # "halt" | "reduce"


class BlackSwanCircuitBreaker:
    THRESHOLDS = {
        "gold_30min_move_pct":   CB_GOLD_30MIN_MOVE_PCT,
        "spread_vs_baseline":    CB_SPREAD_VS_BASELINE,
        "vix_spike_1hr":         CB_VIX_SPIKE_1HR,
        "volume_vs_baseline":    CB_VOLUME_VS_BASELINE,
    }

    def __init__(self):
        self._tripped: CircuitBreakerTrip | None = None
        self._spread_baseline: float | None = None
        self._volume_baseline: float | None = None
        self._prices_30min: list[float] = []

    def update_spread_baseline(self, spread: float):
        if self._spread_baseline is None:
            self._spread_baseline = spread
        else:
            # Rolling EMA
            self._spread_baseline = self._spread_baseline * 0.99 + spread * 0.01

    def update_volume_baseline(self, volume: float):
        if self._volume_baseline is None:
            self._volume_baseline = volume
        else:
            self._volume_baseline = self._volume_baseline * 0.99 + volume * 0.01

    def check_price_move(self, current_price: float) -> CircuitBreakerTrip | None:
        self._prices_30min.append(current_price)
        if len(self._prices_30min) > 30:
            self._prices_30min.pop(0)
        if len(self._prices_30min) < 2:
            return None
        oldest = self._prices_30min[0]
        move_pct = abs(current_price - oldest) / oldest * 100
        if move_pct > self.THRESHOLDS["gold_30min_move_pct"]:
            return self._trip(f"Gold 30min move {move_pct:.2f}% > {self.THRESHOLDS['gold_30min_move_pct']}%")
        return None

    def check_spread(self, current_spread: float) -> CircuitBreakerTrip | None:
        if self._spread_baseline and self._spread_baseline > 0:
            ratio = current_spread / self._spread_baseline
            if ratio > self.THRESHOLDS["spread_vs_baseline"]:
                return self._trip(f"Spread {ratio:.1f}x baseline")
        return None

    def check_volume(self, current_volume: float) -> CircuitBreakerTrip | None:
        if self._volume_baseline and self._volume_baseline > 0:
            ratio = current_volume / self._volume_baseline
            if ratio > self.THRESHOLDS["volume_vs_baseline"]:
                return self._trip(f"Volume {ratio:.1f}x baseline")
        return None

    def is_tripped(self) -> bool:
        return self._tripped is not None

    def reset(self):
        self._tripped = None
        logger.info("Circuit breaker reset")

    def _trip(self, reason: str) -> CircuitBreakerTrip:
        trip = CircuitBreakerTrip(
            reason=reason,
            triggered_at=datetime.now(timezone.utc),
            severity="halt",
        )
        self._tripped = trip
        logger.critical("CIRCUIT BREAKER TRIPPED: %s", reason)
        return trip
