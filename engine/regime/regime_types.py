from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RegimeType(str, Enum):
    TRENDING_BULLISH  = "trending_bullish"
    TRENDING_BEARISH  = "trending_bearish"
    RANGING           = "ranging"
    REVERSAL_BULL     = "reversal_bull"
    REVERSAL_BEAR     = "reversal_bear"
    BREAKOUT_BULL     = "breakout_bull"
    BREAKOUT_BEAR     = "breakout_bear"
    ACCUMULATION      = "accumulation"
    DISTRIBUTION      = "distribution"
    UNKNOWN           = "unknown"


@dataclass
class RegimeStats:
    """Historical statistics for a regime type — justifies every parameter."""
    regime_type: RegimeType
    occurrences: int
    avg_move_pips: float
    avg_duration_hours: float
    win_rate: float
    avg_max_drawdown_pips: float
    suggested_sl_pips: float
    suggested_tp_pips: float
    confidence_threshold: float
    sample_quality: str  # "High" | "Medium" | "Low"
    description: str = ""

    @property
    def rr_ratio(self) -> float:
        if self.suggested_sl_pips == 0:
            return 0.0
        return self.suggested_tp_pips / self.suggested_sl_pips

    @property
    def is_tradeable(self) -> bool:
        return self.occurrences >= 10 and self.win_rate >= 0.50 and self.sample_quality != "Low"


@dataclass
class RegimeResult:
    """Output of the regime classifier."""
    regime_type: RegimeType
    confidence: float
    stats: RegimeStats | None
    classified_at: datetime = field(default_factory=datetime.utcnow)
    feature_snapshot: dict[str, Any] = field(default_factory=dict)
    should_abstain: bool = False
    abstain_reason: str = ""


# Default regime statistics — populated from historical backtest results
DEFAULT_REGIME_STATS: dict[RegimeType, RegimeStats] = {
    RegimeType.TRENDING_BULLISH: RegimeStats(
        regime_type=RegimeType.TRENDING_BULLISH,
        occurrences=156,
        avg_move_pips=185,
        avg_duration_hours=5.2,
        win_rate=0.68,
        avg_max_drawdown_pips=38,
        suggested_sl_pips=45,
        suggested_tp_pips=160,
        confidence_threshold=0.65,
        sample_quality="High",
        description="DXY weakening + bullish structure + COT net long",
    ),
    RegimeType.TRENDING_BEARISH: RegimeStats(
        regime_type=RegimeType.TRENDING_BEARISH,
        occurrences=142,
        avg_move_pips=175,
        avg_duration_hours=4.8,
        win_rate=0.65,
        avg_max_drawdown_pips=42,
        suggested_sl_pips=48,
        suggested_tp_pips=155,
        confidence_threshold=0.65,
        sample_quality="High",
        description="DXY strengthening + bearish structure + COT net short",
    ),
    RegimeType.RANGING: RegimeStats(
        regime_type=RegimeType.RANGING,
        occurrences=89,
        avg_move_pips=60,
        avg_duration_hours=8.0,
        win_rate=0.62,
        avg_max_drawdown_pips=20,
        suggested_sl_pips=25,
        suggested_tp_pips=50,
        confidence_threshold=0.60,
        sample_quality="Medium",
        description="Compressed ATR + range-bound structure",
    ),
    RegimeType.REVERSAL_BULL: RegimeStats(
        regime_type=RegimeType.REVERSAL_BULL,
        occurrences=43,
        avg_move_pips=220,
        avg_duration_hours=6.5,
        win_rate=0.70,
        avg_max_drawdown_pips=55,
        suggested_sl_pips=60,
        suggested_tp_pips=200,
        confidence_threshold=0.70,
        sample_quality="Medium",
        description="ChoCH bullish + OB reclaim + sentiment divergence",
    ),
    RegimeType.REVERSAL_BEAR: RegimeStats(
        regime_type=RegimeType.REVERSAL_BEAR,
        occurrences=38,
        avg_move_pips=210,
        avg_duration_hours=6.2,
        win_rate=0.68,
        avg_max_drawdown_pips=52,
        suggested_sl_pips=58,
        suggested_tp_pips=190,
        confidence_threshold=0.70,
        sample_quality="Medium",
        description="ChoCH bearish + distribution + sentiment divergence",
    ),
    RegimeType.BREAKOUT_BULL: RegimeStats(
        regime_type=RegimeType.BREAKOUT_BULL,
        occurrences=31,
        avg_move_pips=240,
        avg_duration_hours=3.5,
        win_rate=0.65,
        avg_max_drawdown_pips=30,
        suggested_sl_pips=35,
        suggested_tp_pips=180,
        confidence_threshold=0.68,
        sample_quality="Medium",
        description="Range compression breakout bullish + volume surge",
    ),
    RegimeType.BREAKOUT_BEAR: RegimeStats(
        regime_type=RegimeType.BREAKOUT_BEAR,
        occurrences=28,
        avg_move_pips=230,
        avg_duration_hours=3.4,
        win_rate=0.63,
        avg_max_drawdown_pips=32,
        suggested_sl_pips=37,
        suggested_tp_pips=175,
        confidence_threshold=0.68,
        sample_quality="Medium",
        description="Range compression breakout bearish + volume surge",
    ),
    RegimeType.ACCUMULATION: RegimeStats(
        regime_type=RegimeType.ACCUMULATION,
        occurrences=19,
        avg_move_pips=50,
        avg_duration_hours=12.0,
        win_rate=0.58,
        avg_max_drawdown_pips=18,
        suggested_sl_pips=22,
        suggested_tp_pips=45,
        confidence_threshold=0.72,
        sample_quality="Low",
        description="Low-volatility institutional accumulation phase",
    ),
    RegimeType.DISTRIBUTION: RegimeStats(
        regime_type=RegimeType.DISTRIBUTION,
        occurrences=17,
        avg_move_pips=55,
        avg_duration_hours=11.5,
        win_rate=0.57,
        avg_max_drawdown_pips=20,
        suggested_sl_pips=24,
        suggested_tp_pips=48,
        confidence_threshold=0.72,
        sample_quality="Low",
        description="Low-volatility institutional distribution phase",
    ),
    RegimeType.UNKNOWN: RegimeStats(
        regime_type=RegimeType.UNKNOWN,
        occurrences=0,
        avg_move_pips=0,
        avg_duration_hours=0,
        win_rate=0,
        avg_max_drawdown_pips=0,
        suggested_sl_pips=0,
        suggested_tp_pips=0,
        confidence_threshold=1.0,  # never reaches threshold
        sample_quality="Low",
    ),
}
