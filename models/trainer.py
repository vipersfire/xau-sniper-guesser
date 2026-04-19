"""XGBoost regime classifier training pipeline."""
import logging
import numpy as np
from datetime import datetime, timedelta
from models.registry import ModelRegistry
from backtest.validator import purged_walk_forward_splits, compute_recency_weights, validate_model
from engine.regime.classifier import FEATURE_NAMES

logger = logging.getLogger(__name__)


class ModelTrainer:
    def __init__(self):
        self.registry = ModelRegistry()

    async def train(self, years: int = 5):
        from xgboost import XGBClassifier

        logger.info("Loading training data...")
        X, y = await self._build_dataset(years)
        if X is None or len(X) < 100:
            raise ValueError(f"Insufficient training data: {len(X) if X is not None else 0} samples")

        logger.info("Training XGBoost on %d samples, %d features", len(X), X.shape[1])

        model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
        )

        # Recency-weighted training
        weights = compute_recency_weights(len(X), decay_rate=0.001)

        # Walk-forward validation
        logger.info("Running walk-forward validation...")
        cv_results = validate_model(model, X, y, n_splits=5)
        mean_acc = cv_results["mean_test_accuracy"]
        logger.info("Walk-forward mean accuracy: %.1f%% (std=%.1f%%)", mean_acc * 100, cv_results["std_test_accuracy"] * 100)

        if mean_acc < 0.52:
            raise ValueError(f"Model accuracy too low: {mean_acc:.1%} — refusing to save")

        # Final fit on all data
        model.fit(X, y, sample_weight=weights)

        self.registry.save(model, metadata={
            "feature_names": FEATURE_NAMES,
            "cv_results": cv_results,
            "n_samples": len(X),
            "trained_at": datetime.utcnow(),
        })
        logger.info("Model saved. Mean CV accuracy: %.1f%%", mean_acc * 100)
        return cv_results

    async def _build_dataset(self, years: int) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Build (X, y) from historical data. y = regime label."""
        try:
            from data.db import AsyncSessionLocal
            from data.repositories.ohlcv_repo import OHLCVRepository
            from engine.signals.structural import StructuralSignals
            from engine.signals.macro import MacroSignals
            from engine.signals.sentiment import SentimentSignals
            from config.constants import SYMBOL

            start = datetime.utcnow() - timedelta(days=years * 365)
            async with AsyncSessionLocal() as session:
                repo = OHLCVRepository(session)
                bars = await repo.get_bars(SYMBOL, "H1", start)

            if len(bars) < 200:
                return None, None

            struct = StructuralSignals()
            macro_sig = MacroSignals()
            sent_sig = SentimentSignals()

            rows_X, rows_y = [], []
            for i in range(50, len(bars)):
                window = bars[max(0, i - 50): i]
                features = {}
                features.update(struct.extract_features(window))
                features.update(await macro_sig.extract_features())
                features.update(await sent_sig.extract_features())

                label = self._label_bar(bars, i)
                if label is None:
                    continue

                row = [features.get(f, 0.0) for f in FEATURE_NAMES]
                rows_X.append(row)
                rows_y.append(label)

            if not rows_X:
                return None, None

            return np.array(rows_X, dtype=np.float32), np.array(rows_y)

        except Exception as e:
            logger.error("Failed to build dataset: %s", e)
            return None, None

    def _label_bar(self, bars, idx: int, lookahead: int = 8) -> str | None:
        """Label a bar based on subsequent price action."""
        if idx + lookahead >= len(bars):
            return None
        entry_close = bars[idx].close
        future_close = bars[idx + lookahead].close
        move_pct = (future_close - entry_close) / entry_close * 100
        if move_pct > 0.15:
            return "trending_bullish"
        if move_pct < -0.15:
            return "trending_bearish"
        return "ranging"
