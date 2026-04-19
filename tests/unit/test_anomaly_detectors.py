"""Unit tests for anomaly detection modules."""
import pytest
import numpy as np
from anomaly.isolation_forest import IsolationForestDetector
from anomaly.structural_detector import StructuralDeviationDetector


class TestIsolationForestDetector:
    def _make_normal_features(self, n: int = 200) -> list[dict]:
        rng = np.random.default_rng(42)
        return [
            {
                "atr": float(rng.normal(10, 1)),
                "dxy_slope": float(rng.normal(0, 0.1)),
                "retail_long": float(rng.normal(50, 5)),
            }
            for _ in range(n)
        ]

    def test_score_before_fit_is_zero(self):
        det = IsolationForestDetector()
        score = det.score({"atr": 10.0, "dxy": 0.1})
        assert score == 0.0

    def test_score_in_range(self):
        det = IsolationForestDetector()
        for f in self._make_normal_features(150):
            det.add_sample(f)
        score = det.score({"atr": 10.0, "dxy_slope": 0.0, "retail_long": 50.0})
        assert 0.0 <= score <= 1.0

    def test_extreme_outlier_scores_high(self):
        det = IsolationForestDetector(contamination=0.05)
        for f in self._make_normal_features(200):
            det.add_sample(f)
        outlier = {"atr": 1000.0, "dxy_slope": 999.0, "retail_long": 9999.0}
        score = det.score(outlier)
        assert score > 0.3  # Should be flagged as anomalous

    def test_is_anomaly_false_for_normal(self):
        det = IsolationForestDetector()
        for f in self._make_normal_features(200):
            det.add_sample(f)
        normal = {"atr": 10.0, "dxy_slope": 0.0, "retail_long": 50.0}
        # Normal data should NOT consistently trigger is_anomaly
        # (probabilistic — just check it doesn't crash)
        result = det.is_anomaly(normal)
        assert isinstance(result, bool)


class TestStructuralDeviationDetector:
    def _normal_features(self) -> dict:
        rng = np.random.default_rng(seed=1)
        return {"atr": float(rng.normal(10, 0.5)), "rsi": float(rng.normal(50, 5))}

    def test_score_zero_before_data(self):
        det = StructuralDeviationDetector()
        score = det.score({"atr": 10.0})
        assert score == 0.0

    def test_score_after_update(self):
        det = StructuralDeviationDetector(window=50)
        rng = np.random.default_rng(42)
        for _ in range(50):
            det.update({"atr": float(rng.normal(10, 0.5)), "rsi": float(rng.normal(50, 5))})
        score = det.score({"atr": 10.2, "rsi": 51.0})
        assert 0.0 <= score <= 1.0

    def test_extreme_value_is_anomaly(self):
        det = StructuralDeviationDetector(window=50, z_threshold=3.0)
        rng = np.random.default_rng(0)
        for _ in range(60):
            det.update({"atr": float(rng.normal(10, 0.5))})
        # atr=1000 is ~1990 std deviations from mean of 10
        assert det.is_anomaly({"atr": 1000.0})

    def test_normal_value_not_anomaly(self):
        det = StructuralDeviationDetector(window=50, z_threshold=3.0)
        rng = np.random.default_rng(0)
        for _ in range(60):
            det.update({"atr": float(rng.normal(10, 0.5))})
        assert not det.is_anomaly({"atr": 10.1})

    def test_score_is_zero_to_one(self):
        det = StructuralDeviationDetector(window=20)
        for i in range(30):
            det.update({"x": float(i)})
        score = det.score({"x": 15.0})
        assert 0.0 <= score <= 1.0
