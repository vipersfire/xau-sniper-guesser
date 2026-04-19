"""Historical analogue matching — runs parallel to XGBoost when confidence is low."""
import logging
import numpy as np
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HistoricalAnalogue:
    regime_type: str
    similarity: float
    avg_move_pips: float
    win_rate: float
    sl_pips: float
    tp_pips: float
    event_date: str


@dataclass
class TradeParameters:
    direction: str
    sl_pips: float
    tp_pips: float
    confidence: float
    source: str = "analogy"


class AnalogyEngine:
    """Cosine-similarity search over normalized feature vectors of past regimes."""

    def __init__(self):
        self._library: list[dict[str, Any]] = []

    def add_to_library(self, features: dict[str, float], outcome: dict[str, Any]):
        vec = list(features.values())
        self._library.append({"features": vec, "outcome": outcome})

    def find_analogues(
        self,
        current_features: dict[str, float],
        min_similarity: float = 0.75,
        max_results: int = 5,
    ) -> list[HistoricalAnalogue]:
        if not self._library:
            return []
        query = np.array(list(current_features.values()), dtype=float)
        query_norm = _norm(query)
        results = []
        for entry in self._library:
            vec = np.array(entry["features"], dtype=float)
            sim = float(np.dot(query_norm, _norm(vec)))
            if sim >= min_similarity:
                out = entry["outcome"]
                results.append(HistoricalAnalogue(
                    regime_type=out.get("regime_type", "unknown"),
                    similarity=sim,
                    avg_move_pips=out.get("move_pips", 0),
                    win_rate=out.get("win_rate", 0),
                    sl_pips=out.get("sl_pips", 50),
                    tp_pips=out.get("tp_pips", 100),
                    event_date=out.get("date", ""),
                ))
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:max_results]

    def derive_parameters(self, analogues: list[HistoricalAnalogue]) -> TradeParameters | None:
        if not analogues:
            return None
        weights = np.array([a.similarity for a in analogues])
        weights /= weights.sum()
        sl = float(np.average([a.sl_pips for a in analogues], weights=weights))
        tp = float(np.average([a.tp_pips for a in analogues], weights=weights))
        win_rate = float(np.average([a.win_rate for a in analogues], weights=weights))
        # direction from most common regime
        directions = [a.regime_type for a in analogues]
        direction = "buy" if directions.count("trending_bullish") + directions.count("reversal_bull") > len(directions) / 2 else "sell"
        return TradeParameters(direction=direction, sl_pips=sl, tp_pips=tp, confidence=win_rate)


def _norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > 0 else v
