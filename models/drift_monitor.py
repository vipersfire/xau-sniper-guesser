"""PSI-based feature drift monitoring and rolling accuracy tracking."""
import logging
import numpy as np
from collections import deque
from utils.math_utils import psi
from config.constants import PSI_WATCH, PSI_INVESTIGATE, PSI_CRITICAL

logger = logging.getLogger(__name__)


class DriftMonitor:
    def __init__(self, window_size: int = 500):
        self._reference: np.ndarray | None = None
        self._rolling_window: deque = deque(maxlen=window_size)
        self._accuracy_window: deque = deque(maxlen=100)

    def set_reference(self, X: np.ndarray):
        self._reference = X

    def add_sample(self, features: np.ndarray, predicted: str, actual: str | None = None):
        self._rolling_window.append(features)
        if actual is not None:
            self._accuracy_window.append(int(predicted == actual))

    def compute_psi_per_feature(self) -> dict[str, float]:
        if self._reference is None or len(self._rolling_window) < 50:
            return {}
        current = np.array(list(self._rolling_window))
        results = {}
        for i in range(self._reference.shape[1]):
            try:
                p = psi(self._reference[:, i], current[:, i])
                results[f"feature_{i}"] = round(p, 4)
            except Exception:
                pass
        return results

    def drift_level(self, feature_psi: dict[str, float]) -> str:
        if not feature_psi:
            return "unknown"
        max_psi = max(feature_psi.values())
        if max_psi > PSI_CRITICAL:
            return "critical"
        if max_psi > PSI_INVESTIGATE:
            return "significant"
        if max_psi > PSI_WATCH:
            return "minor"
        return "stable"

    def rolling_accuracy(self) -> float:
        if not self._accuracy_window:
            return 0.0
        return float(np.mean(list(self._accuracy_window)))

    def check(self) -> dict:
        psi_vals = self.compute_psi_per_feature()
        level = self.drift_level(psi_vals)
        acc = self.rolling_accuracy()
        if level == "critical":
            logger.warning("CRITICAL drift detected (max PSI=%.3f) — retraining recommended", max(psi_vals.values()) if psi_vals else 0)
        return {
            "drift_level": level,
            "rolling_accuracy": round(acc, 3),
            "psi_values": psi_vals,
            "needs_retrain": level in ("critical", "significant"),
        }
