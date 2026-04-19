"""Combinatorial Purged Cross-Validation + Walk-Forward validation."""
import logging
import numpy as np
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CVFold:
    train_indices: np.ndarray
    test_indices: np.ndarray
    fold_id: int


def purged_walk_forward_splits(
    n_samples: int,
    n_splits: int = 5,
    purge_bars: int = 5,
    embargo_bars: int = 10,
) -> list[CVFold]:
    """
    Walk-forward with anchored origin.
    Train always starts at 0. Test window moves forward.
    Purge: remove bars near split. Embargo: gap between train and test.
    """
    folds = []
    test_size = n_samples // (n_splits + 1)

    for i in range(n_splits):
        test_start = (i + 1) * test_size
        test_end = test_start + test_size
        if test_end > n_samples:
            break

        train_end = test_start - embargo_bars
        if train_end <= 0:
            continue

        # Purge: remove samples too close to split point
        train_indices = np.arange(0, train_end - purge_bars)
        test_indices = np.arange(test_start, min(test_end, n_samples))

        if len(train_indices) < 50 or len(test_indices) < 10:
            continue

        folds.append(CVFold(
            train_indices=train_indices,
            test_indices=test_indices,
            fold_id=i,
        ))
        logger.debug("Fold %d: train[0:%d] test[%d:%d]", i, train_end, test_start, test_end)

    return folds


def compute_recency_weights(
    n_samples: int,
    decay_rate: float = 0.001,
) -> np.ndarray:
    """More recent samples get higher weight."""
    ages = np.arange(n_samples - 1, -1, -1)
    weights = np.exp(-decay_rate * ages)
    return weights / weights.sum() * n_samples  # normalize so sum ≈ n_samples


def validate_model(model, X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> dict[str, Any]:
    """Run purged walk-forward CV, return per-fold and aggregate stats."""
    from sklearn.metrics import accuracy_score
    folds = purged_walk_forward_splits(len(X), n_splits=n_splits)
    fold_results = []

    for fold in folds:
        X_train, y_train = X[fold.train_indices], y[fold.train_indices]
        X_test, y_test = X[fold.test_indices], y[fold.test_indices]
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        fold_results.append({"fold": fold.fold_id, "test_accuracy": acc, "n_test": len(y_test)})

    accs = [r["test_accuracy"] for r in fold_results]
    return {
        "folds": fold_results,
        "mean_test_accuracy": float(np.mean(accs)),
        "std_test_accuracy": float(np.std(accs)),
        "min_test_accuracy": float(np.min(accs)),
    }
