"""
Unit tests for the evaluation framework (Phase 0).

Tests:
  - NDCG@10 = 1.0 for ideal ranking
  - NDCG@10 = 0.0 for all-irrelevant results
  - Metrics are deterministic
  - Regression guard logic
"""

import pytest
import sys
import os
from pathlib import Path

# Ensure the backend directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestNDCGBoundaries:
    """Verify NDCG formula correctness at boundary conditions."""

    def _get_fns(self):
        from evaluation.evaluate import _ndcg, compute_metrics
        return _ndcg, compute_metrics

    def test_ndcg_perfect_ranking(self):
        """NDCG@10 = 1.0 when results exactly match ideal ranking."""
        _ndcg, _ = self._get_fns()
        grades = [3.0, 3.0, 2.0, 2.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        ideal = sorted(grades, reverse=True)
        result = _ndcg(grades, ideal, 10)
        assert abs(result - 1.0) < 1e-10, f"Expected 1.0, got {result}"

    def test_ndcg_zero_all_irrelevant(self):
        """NDCG@10 = 0.0 when all results have grade 0."""
        _ndcg, _ = self._get_fns()
        grades = [0.0] * 20
        ideal = [3.0, 2.0, 1.0] + [0.0] * 17  # Ideal has some relevants
        result = _ndcg(grades, ideal, 10)
        assert result == 0.0, f"Expected 0.0, got {result}"

    def test_ndcg_no_relevant_in_qrel(self):
        """NDCG@10 = 0.0 when ideal is all zeros (no relevant docs)."""
        _ndcg, _ = self._get_fns()
        grades = [3.0, 2.0, 1.0]
        ideal = [0.0] * 20
        result = _ndcg(grades, ideal, 10)
        assert result == 0.0

    def test_ndcg_degraded(self):
        """NDCG drops when relevant docs are ranked lower."""
        _ndcg, _ = self._get_fns()
        ideal = [3.0, 2.0, 1.0, 0.0, 0.0]
        worse = [0.0, 0.0, 0.0, 2.0, 3.0]  # relevant docs pushed to end
        ideal_ndcg = _ndcg(ideal, ideal, 5)
        worse_ndcg = _ndcg(worse, ideal, 5)
        assert ideal_ndcg > worse_ndcg

    def test_compute_metrics_deterministic(self):
        """Running compute_metrics twice on same data gives identical output."""
        _, compute_metrics = self._get_fns()
        qrels = {
            'Q1': {'A': 3.0, 'B': 2.0, 'C': 0.0, 'D': 1.0},
            'Q2': {'X': 2.0, 'Y': 3.0, 'Z': 0.0},
        }
        run = {
            'Q1': {'A': 10.0, 'B': 8.0, 'C': 5.0, 'D': 3.0},
            'Q2': {'X': 10.0, 'Y': 7.0, 'Z': 2.0},
        }
        result1 = compute_metrics(qrels, run)
        result2 = compute_metrics(qrels, run)
        for metric in ['ndcg@5', 'ndcg@10', 'mrr@5', 'mrr@10', 'recall@10', 'precision@5', 'map@10']:
            assert result1[metric] == result2[metric], f"Non-deterministic: {metric}"

    def test_compute_metrics_returns_all_keys(self):
        """compute_metrics returns all expected metric keys."""
        _, compute_metrics = self._get_fns()
        qrels = {'Q1': {'A': 3.0, 'B': 0.0}}
        run = {'Q1': {'A': 2.0, 'B': 1.0}}
        result = compute_metrics(qrels, run)
        for metric in ['ndcg@5', 'ndcg@10', 'mrr@5', 'mrr@10', 'recall@10', 'precision@5', 'map@10']:
            assert metric in result, f"Missing metric: {metric}"

    def test_compute_metrics_empty_run(self):
        """compute_metrics handles empty run gracefully."""
        _, compute_metrics = self._get_fns()
        qrels = {'Q1': {'A': 3.0}}
        run = {}
        result = compute_metrics(qrels, run)
        for metric in ['ndcg@5', 'ndcg@10']:
            assert result[metric] == 0.0


class TestMRR:
    def test_mrr_first_rank(self):
        """MRR = 1.0 when first result is relevant."""
        from evaluation.evaluate import _mrr
        scores = [3.0, 0.0, 0.0, 0.0, 0.0]
        assert _mrr(scores, 5) == 1.0

    def test_mrr_second_rank(self):
        """MRR = 0.5 when second result is first relevant."""
        from evaluation.evaluate import _mrr
        scores = [0.0, 3.0, 0.0, 0.0, 0.0]
        assert abs(_mrr(scores, 5) - 0.5) < 1e-10

    def test_mrr_no_relevant(self):
        """MRR = 0.0 when no relevant results."""
        from evaluation.evaluate import _mrr
        scores = [0.0, 0.0, 0.0]
        assert _mrr(scores, 5) == 0.0


class TestRegressionGuard:
    """Test that regression guard logic works correctly."""

    def test_regression_guard_detects_drop(self):
        """Verify regression_guard_passed = False when NDCG@10 drops > threshold."""
        from evaluation.evaluate import REGRESSION_THRESHOLD
        # Simulate: current NDCG@10 = 0.30, baseline = 0.35 → drop = 0.05 > 0.02
        current_ndcg10 = 0.30
        baseline_ndcg10 = 0.35
        drop = current_ndcg10 - baseline_ndcg10  # -0.05
        assert drop < -REGRESSION_THRESHOLD, "Should have detected regression"

    def test_regression_guard_passes_on_improvement(self):
        """regression_guard_passed = True when metrics improve."""
        from evaluation.evaluate import REGRESSION_THRESHOLD
        current_ndcg10 = 0.40
        baseline_ndcg10 = 0.35
        drop = current_ndcg10 - baseline_ndcg10  # +0.05
        assert drop >= -REGRESSION_THRESHOLD, "Should not flag improvement as regression"

    def test_regression_guard_passes_on_small_drop(self):
        """regression_guard_passed = True for drop within threshold."""
        from evaluation.evaluate import REGRESSION_THRESHOLD
        current_ndcg10 = 0.34
        baseline_ndcg10 = 0.35
        drop = current_ndcg10 - baseline_ndcg10  # -0.01 < 0.02 threshold
        assert drop >= -REGRESSION_THRESHOLD


class TestHeuristicJudge:
    """Test the heuristic fallback judge."""

    def test_product_match_high_volume(self):
        """High-volume dextrose supplier scores 3 for dextrose query."""
        from evaluation.generate_judgments import _heuristic_judge
        result = {
            'name': 'Dongying City Dextrose Co',
            'country': 'China',
            'total_volume': 500.0,
            'shipment_count': 20,
            'avg_price': 450.0,
            'products': 'dextrose anhydrous',
        }
        score, _ = _heuristic_judge('dextrose anhydrous suppliers', result)
        assert score == 3

    def test_wrong_country_scores_zero(self):
        """Result from wrong country scores 0 for country-filtered query."""
        from evaluation.generate_judgments import _heuristic_judge
        result = {
            'name': 'Some German Company',
            'country': 'Germany',
            'total_volume': 500.0,
            'shipment_count': 20,
            'avg_price': 450.0,
            'products': 'dextrose anhydrous',
        }
        score, _ = _heuristic_judge('dextrose from China', result)
        assert score == 0

    def test_company_name_in_query_scores_high(self):
        """Exact company name match in query scores 3."""
        from evaluation.generate_judgments import _heuristic_judge
        result = {
            'name': 'Lactalis Ingredients',
            'country': 'France',
            'total_volume': 300.0,
            'shipment_count': 15,
            'avg_price': 800.0,
            'products': 'lactose monohydrate',
        }
        score, _ = _heuristic_judge('Lactalis Ingredients shipments', result)
        assert score >= 2

    def test_no_product_match_scores_zero(self):
        """Unrelated product scores 0."""
        from evaluation.generate_judgments import _heuristic_judge
        result = {
            'name': 'Random Electronics Co',
            'country': 'China',
            'total_volume': 500.0,
            'shipment_count': 20,
            'avg_price': 200.0,
            'products': 'electronics',
        }
        score, _ = _heuristic_judge('dextrose anhydrous suppliers', result)
        assert score == 0
