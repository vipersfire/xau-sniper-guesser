from dataclasses import dataclass, field
from enum import Enum


class DataQualityFlag(str, Enum):
    INTERPOLATED = "INTERPOLATED"
    GAP_ADJACENT = "GAP_ADJACENT"
    HIGH_SPREAD = "HIGH_SPREAD"
    NEWS_ADJACENT = "NEWS_ADJACENT"
    LOW_VOLUME = "LOW_VOLUME"
    WEEKEND_EDGE = "WEEKEND_EDGE"


@dataclass
class OHLCVQuality:
    quality_score: float = 1.0
    flags: set[DataQualityFlag] = field(default_factory=set)

    def penalize(self, flag: DataQualityFlag, penalty: float = 0.1):
        self.flags.add(flag)
        self.quality_score = max(0.0, self.quality_score - penalty)

    @property
    def is_usable(self) -> bool:
        return self.quality_score >= 0.5

    @property
    def is_high_quality(self) -> bool:
        return self.quality_score >= 0.9 and not self.flags


def score_bar(
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
    spread: float,
    prev_close: float | None = None,
    avg_spread: float | None = None,
    avg_volume: float | None = None,
    is_news_adjacent: bool = False,
    is_weekend_edge: bool = False,
) -> OHLCVQuality:
    q = OHLCVQuality()

    # Basic OHLCV sanity
    if high < low or high < open_ or high < close or low > open_ or low > close:
        q.penalize(DataQualityFlag.INTERPOLATED, 0.5)

    # Gap detection
    if prev_close is not None and abs(open_ - prev_close) / max(prev_close, 1e-9) > 0.005:
        q.penalize(DataQualityFlag.GAP_ADJACENT, 0.15)

    if avg_spread and spread > avg_spread * 3:
        q.penalize(DataQualityFlag.HIGH_SPREAD, 0.1)

    if avg_volume and volume < avg_volume * 0.1:
        q.penalize(DataQualityFlag.LOW_VOLUME, 0.1)

    if is_news_adjacent:
        q.penalize(DataQualityFlag.NEWS_ADJACENT, 0.05)

    if is_weekend_edge:
        q.penalize(DataQualityFlag.WEEKEND_EDGE, 0.05)

    return q
