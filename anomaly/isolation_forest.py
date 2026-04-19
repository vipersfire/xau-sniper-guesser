"""Detector A: Isolation Forest on feature vector."""
import logging
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class IsolationForestDetector:
    def __init__(self, contamination: float = 0.05):
        self._model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
        self._fitted = False
        self._history: list[list[float]] = []
        self._min_fit_samples = 100

    def add_sample(self, features: dict[str, float]):
        vec = list(features.values())
        self._history.append(vec)
        if len(self._history) % 50 == 0:
            self._fit()

    def _fit(self):
        if len(self._history) < self._min_fit_samples:
            return
        X = np.array(self._history[-2000:])  # Use last 2000 samples
        self._model.fit(X)
        self._fitted = True

    def score(self, features: dict[str, float]) -> float:
        """Returns anomaly score [0, 1]. Higher = more anomalous."""
        if not self._fitted:
            return 0.0
        vec = np.array(list(features.values())).reshape(1, -1)
        try:
            raw_score = self._model.score_samples(vec)[0]
            # IsolationForest returns negative scores. More negative = more anomalous.
            # Normalize to [0, 1]
            normalized = max(0.0, min(1.0, (-raw_score - 0.1) / 0.5))
            return float(normalized)
        except Exception as e:
            logger.warning("Isolation Forest score failed: %s", e)
            return 0.0

    def is_anomaly(self, features: dict[str, float], threshold: float = 0.5) -> bool:
        return self.score(features) >= threshold
