"""XGBoost + rule-based hybrid regime classifier."""
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any

import numpy as np

from engine.regime.regime_types import RegimeType, RegimeResult, DEFAULT_REGIME_STATS
from engine.regime.confidence import should_abstain

logger = logging.getLogger(__name__)

# Features used by the XGBoost model (must match training)
FEATURE_NAMES = [
    "dxy_slope_h4",
    "real_yield_10y",
    "cot_net_noncomm_norm",
    "retail_long_pct",
    "atr_14_h1",
    "atr_14_d1",
    "atr_ratio",          # h1 / d1 ATR
    "ob_distance_pips",   # distance to nearest order block
    "fvg_present",        # 1 if FVG in range, else 0
    "bos_recent",         # 1 if BOS in last 4 bars
    "choch_recent",       # 1 if ChoCH in last 4 bars
    "session_asian",
    "session_london",
    "session_ny",
    "session_overlap",
    "price_vs_ema50",     # normalized
    "price_vs_ema200",
    "rsi_h1",
    "news_pressure_score",
]


def _classify_in_process(model_artifact: dict, features: np.ndarray) -> tuple[str, float, list[float]]:
    """CPU-bound work — runs in separate process to bypass GIL."""
    model = model_artifact["model"]
    probs = model.predict_proba(features.reshape(1, -1))[0]
    class_idx = int(np.argmax(probs))
    classes = model.classes_
    regime_str = classes[class_idx] if class_idx < len(classes) else "unknown"
    confidence = float(probs[class_idx])
    return regime_str, confidence, probs.tolist()


class RegimeClassifier:
    def __init__(self):
        self._executor = ProcessPoolExecutor(max_workers=1)
        self._model_artifact: dict | None = None
        self._load_model()

    def _load_model(self):
        try:
            from models.loader import ModelLoader
            loader = ModelLoader()
            self._model_artifact = loader.load()
            logger.info("Regime classifier model loaded")
        except Exception as e:
            logger.warning("Could not load regime classifier: %s — using rule-based fallback", e)
            self._model_artifact = None

    async def classify(self, features: dict[str, float]) -> RegimeResult:
        feature_vec = np.array([features.get(f, 0.0) for f in FEATURE_NAMES], dtype=np.float32)

        regime_type = RegimeType.UNKNOWN
        confidence = 0.0

        if self._model_artifact is not None:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                regime_str, confidence, probs = await loop.run_in_executor(
                    self._executor,
                    _classify_in_process,
                    self._model_artifact,
                    feature_vec,
                )
                regime_type = RegimeType(regime_str) if regime_str in RegimeType._value2member_map_ else RegimeType.UNKNOWN
            except Exception as e:
                logger.error("ML classify failed: %s — falling back to rules", e)
                regime_type, confidence = self._rule_based_fallback(features)
        else:
            regime_type, confidence = self._rule_based_fallback(features)

        stats = DEFAULT_REGIME_STATS.get(regime_type)
        result = RegimeResult(
            regime_type=regime_type,
            confidence=confidence,
            stats=stats,
            feature_snapshot=features,
        )
        abstain, reason = should_abstain(result)
        result.should_abstain = abstain
        result.abstain_reason = reason
        return result

    def _rule_based_fallback(self, features: dict[str, float]) -> tuple[RegimeType, float]:
        """Simple deterministic rules when ML model unavailable."""
        dxy_slope = features.get("dxy_slope_h4", 0)
        atr_ratio = features.get("atr_ratio", 1.0)
        bos = features.get("bos_recent", 0)
        choch = features.get("choch_recent", 0)
        cot_net = features.get("cot_net_noncomm_norm", 0)
        retail_long = features.get("retail_long_pct", 50)

        if choch > 0 and cot_net > 0.3 and dxy_slope < -0.1:
            return RegimeType.REVERSAL_BULL, 0.62
        if choch > 0 and cot_net < -0.3 and dxy_slope > 0.1:
            return RegimeType.REVERSAL_BEAR, 0.62
        if bos > 0 and dxy_slope < -0.05 and cot_net > 0.1:
            return RegimeType.TRENDING_BULLISH, 0.60
        if bos > 0 and dxy_slope > 0.05 and cot_net < -0.1:
            return RegimeType.TRENDING_BEARISH, 0.60
        if atr_ratio < 0.7:
            return RegimeType.RANGING, 0.58
        return RegimeType.UNKNOWN, 0.0

    def reload(self):
        self._load_model()

    def shutdown(self):
        self._executor.shutdown(wait=False)
