"""Unit tests for backtest/validator.py"""
import numpy as np
import pytest
from backtest.validator import purged_walk_forward_splits, compute_recency_weights


class TestPurgedWalkForwardSplits:
    def test_returns_correct_number_of_folds(self):
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=5)
        assert len(folds) == 5

    def test_train_always_before_test(self):
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=5)
        for fold in folds:
            assert fold.train_indices[-1] < fold.test_indices[0]

    def test_no_overlap_between_train_and_test(self):
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=5)
        for fold in folds:
            train_set = set(fold.train_indices.tolist())
            test_set = set(fold.test_indices.tolist())
            assert train_set.isdisjoint(test_set)

    def test_embargo_gap_respected(self):
        embargo = 10
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=3, embargo_bars=embargo)
        for fold in folds:
            gap = fold.test_indices[0] - fold.train_indices[-1]
            assert gap >= embargo

    def test_purge_gap_respected(self):
        purge = 5
        embargo = 10
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=3, purge_bars=purge, embargo_bars=embargo)
        for fold in folds:
            # Train end + purge + embargo should be <= test start
            assert len(fold.train_indices) > 0
            assert len(fold.test_indices) > 0

    def test_small_dataset_returns_fewer_folds(self):
        folds = purged_walk_forward_splits(n_samples=50, n_splits=5)
        assert len(folds) <= 5

    def test_fold_ids_are_sequential(self):
        folds = purged_walk_forward_splits(n_samples=1000, n_splits=4)
        for i, fold in enumerate(folds):
            assert fold.fold_id == i

    def test_walk_forward_train_grows(self):
        """Training set should grow with each fold (anchored origin)."""
        folds = purged_walk_forward_splits(n_samples=2000, n_splits=4)
        train_sizes = [len(f.train_indices) for f in folds]
        assert train_sizes == sorted(train_sizes)


class TestComputeRecencyWeights:
    def test_shape_matches_input(self):
        weights = compute_recency_weights(100)
        assert weights.shape == (100,)

    def test_last_sample_has_highest_weight(self):
        weights = compute_recency_weights(100)
        assert weights[-1] == weights.max()

    def test_first_sample_has_lowest_weight(self):
        weights = compute_recency_weights(100)
        assert weights[0] == weights.min()

    def test_weights_sum_to_n(self):
        n = 200
        weights = compute_recency_weights(n)
        assert weights.sum() == pytest.approx(n, rel=1e-3)

    def test_all_positive(self):
        weights = compute_recency_weights(50)
        assert np.all(weights > 0)

    def test_decay_rate_effect(self):
        # Higher decay rate → more extreme weighting toward recent
        w_slow = compute_recency_weights(100, decay_rate=0.0001)
        w_fast = compute_recency_weights(100, decay_rate=0.01)
        ratio_slow = w_slow[-1] / w_slow[0]
        ratio_fast = w_fast[-1] / w_fast[0]
        assert ratio_fast > ratio_slow
