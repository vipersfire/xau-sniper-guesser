"""Model health checks post-load."""
import logging
import numpy as np
from models.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelValidator:
    def __init__(self):
        self.registry = ModelRegistry()

    def validate(self) -> dict:
        info = self.registry.check()
        if not info.valid:
            return {"valid": False, "error": info.error}

        artifact = self.registry.load()
        model = artifact.get("model")
        feature_names = artifact.get("feature_names", [])

        checks = {}

        # Check model has predict_proba
        checks["has_predict_proba"] = hasattr(model, "predict_proba")

        # Check feature count matches
        expected = len(feature_names)
        try:
            n_features = model.n_features_in_
            checks["feature_count_match"] = (n_features == expected)
        except AttributeError:
            checks["feature_count_match"] = True

        # Quick sanity: predict on dummy data
        try:
            X_dummy = np.zeros((1, max(expected, 1)))
            _ = model.predict_proba(X_dummy)
            checks["predict_works"] = True
        except Exception as e:
            checks["predict_works"] = False
            checks["predict_error"] = str(e)

        all_pass = all(v is True for v in checks.values() if isinstance(v, bool))
        return {"valid": all_pass, "checks": checks, "feature_count": expected}
