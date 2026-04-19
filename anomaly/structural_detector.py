"""Detector B: Structural price behavior deviation from known regime templates."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class StructuralDeviationDetector:
    """Z-score deviation of price features from rolling baseline."""

    def __init__(self, window: int = 200, z_threshold: float = 3.0):
        self._window = window
        self._z_threshold = z_threshold
        self._buffers: dict[str, list[float]] = {}

    def update(self, features: dict[str, float]):
        for k, v in features.items():
            if k not in self._buffers:
                self._buffers[k] = []
            self._buffers[k].append(v)
            if len(self._buffers[k]) > self._window:
                self._buffers[k].pop(0)

    def score(self, features: dict[str, float]) -> float:
        """Returns anomaly score [0, 1] based on max z-score across features."""
        max_z = 0.0
        for k, v in features.items():
            buf = self._buffers.get(k, [])
            if len(buf) < 10:
                continue
            arr = np.array(buf)
            std = arr.std()
            if std == 0:
                continue
            z = abs(v - arr.mean()) / std
            max_z = max(max_z, z)
        score = min(1.0, max_z / (self._z_threshold * 2))
        return float(score)

    def is_anomaly(self, features: dict[str, float]) -> bool:
        for k, v in features.items():
            buf = self._buffers.get(k, [])
            if len(buf) < 10:
                continue
            arr = np.array(buf)
            std = arr.std()
            if std == 0:
                continue
            z = abs(v - arr.mean()) / std
            if z > self._z_threshold:
                logger.warning("Structural anomaly: feature=%s z=%.1f", k, z)
                return True
        return False
