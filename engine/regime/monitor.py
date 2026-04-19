import logging
from datetime import datetime
from typing import Any
from engine.regime.classifier import RegimeClassifier
from engine.regime.regime_types import RegimeResult, RegimeType

logger = logging.getLogger(__name__)

MAX_HISTORY = 96  # 24h at 15min bars


class RegimeMonitor:
    """Wakes on candle close, runs classifier, maintains history."""

    def __init__(self):
        self.classifier = RegimeClassifier()
        self._current: RegimeResult | None = None
        self.history: list[dict] = []
        self.last_features: dict[str, Any] = {}
        self.last_anomaly_score: float = 0.0

    async def update(self, features: dict[str, float], anomaly_score: float = 0.0) -> RegimeResult:
        self.last_features = features
        self.last_anomaly_score = anomaly_score
        result = await self.classifier.classify(features)
        self._current = result
        self.history.append({
            "time": datetime.utcnow().isoformat(),
            "regime_type": result.regime_type.value,
            "confidence": result.confidence,
            "anomaly_score": anomaly_score,
        })
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
        logger.info(
            "Regime: %s conf=%.1f%% anomaly=%.3f abstain=%s",
            result.regime_type.value,
            result.confidence * 100,
            anomaly_score,
            result.should_abstain,
        )
        return result

    def current_state(self) -> dict:
        if not self._current:
            return {"regime_type": "unknown", "confidence": 0.0, "anomaly_score": 0.0}
        return {
            "regime_type": self._current.regime_type.value,
            "confidence": self._current.confidence,
            "anomaly_score": self.last_anomaly_score,
            "should_abstain": self._current.should_abstain,
            "abstain_reason": self._current.abstain_reason,
        }

    @property
    def current(self) -> RegimeResult | None:
        return self._current
