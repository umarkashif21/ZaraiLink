"""
backend/evaluation/evaluate.py

Evaluation engine for Zarailink search quality.

Metrics computed: NDCG@5, NDCG@10, MRR@5, MRR@10, Recall@10, Precision@5, MAP@10

Usage (standalone):
    cd backend && python evaluation/evaluate.py
    cd backend && python evaluation/evaluate.py --compare-to results/eval_2024-01-01_00-00.json

Usage (via management command):
    python manage.py evaluate_search
    python manage.py evaluate_search --compare-to=eval_2024-01-01_00-00.json
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BASE_DIR = Path(__file__).resolve().parent
JUDGMENTS_PATH = BASE_DIR / 'golden_judgments.json'
GOLDEN_QUERIES_PATH = BASE_DIR / 'golden_queries.json'
RESULTS_DIR = BASE_DIR / 'results'

# Target thresholds — must exceed these to pass
TARGETS = {
    'ndcg@5':      0.40,
    'ndcg@10':     0.38,
    'mrr@5':       0.45,
    'mrr@10':      0.43,
    'recall@10':   0.45,
    'precision@5': 0.40,
    'map@10':      0.35,
}

REGRESSION_THRESHOLD = 0.02  # NDCG@10 must not drop more than this vs baseline


def _setup_django():
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    import django
    django.setup()


# ---------------------------------------------------------------------------
# Metric calculation (native, no dependency on ranx for core correctness tests)
# ---------------------------------------------------------------------------

def _dcg(scores: list[float], k: int) -> float:
    """Discounted Cumulative Gain at k."""
    import math
    result = 0.0
    for i, s in enumerate(scores[:k]):
        result += (2 ** s - 1) / math.log2(i + 2)
    return result


def _ndcg(actual_scores: list[float], ideal_scores: list[float], k: int) -> float:
    """Normalised DCG at k."""
    ideal = sorted(ideal_scores, reverse=True)
    idcg = _dcg(ideal, k)
    if idcg == 0:
        return 0.0
    return _dcg(actual_scores, k) / idcg


def _mrr(actual_scores: list[float], k: int, threshold: float = 1.0) -> float:
    """Mean Reciprocal Rank at k (first relevant item with score >= threshold)."""
    for i, s in enumerate(actual_scores[:k]):
        if s >= threshold:
            return 1.0 / (i + 1)
    return 0.0


def _precision_at_k(actual_scores: list[float], k: int, threshold: float = 1.0) -> float:
    relevant = sum(1 for s in actual_scores[:k] if s >= threshold)
    return relevant / k


def _recall_at_k(actual_scores: list[float], all_relevant: int, k: int, threshold: float = 1.0) -> float:
    if all_relevant == 0:
        return 0.0
    found = sum(1 for s in actual_scores[:k] if s >= threshold)
    return found / all_relevant


def _average_precision(actual_scores: list[float], k: int, threshold: float = 1.0) -> float:
    relevant_count = 0
    precision_sum = 0.0
    for i, s in enumerate(actual_scores[:k]):
        if s >= threshold:
            relevant_count += 1
            precision_sum += relevant_count / (i + 1)
    total_relevant = sum(1 for s in actual_scores if s >= threshold)
    if total_relevant == 0:
        return 0.0
    return precision_sum / total_relevant


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------

def compute_metrics(qrels: dict, run: dict) -> dict:
    """
    Compute all metrics.

    Args:
        qrels: {query_id: {result_id: relevance_score (0-3)}}
        run:   {query_id: {result_id: rank_score}} (higher = better rank)

    Returns:
        dict with per-metric averages across all queries.
    """
    per_query = {}
    skipped_no_judgments = []

    for qid, qrel in qrels.items():
        if qid not in run:
            continue

        # Skip queries with no relevance judgments — these have no ground truth
        # and cannot contribute meaningful signal to any metric.
        # Standard Cranfield evaluation practice: unevaluable queries are excluded.
        all_relevant_count = sum(1 for s in qrel.values() if s >= 1)
        if not qrel or all_relevant_count == 0:
            skipped_no_judgments.append(qid)
            continue

        # Sort run results by descending score (rank 1 first)
        ranked = sorted(run[qid].items(), key=lambda x: x[1], reverse=True)
        result_ids_in_order = [r[0] for r in ranked]

        actual_grades = [float(qrel.get(rid, 0)) for rid in result_ids_in_order]
        ideal_grades = sorted(qrel.values(), reverse=True)

        per_query[qid] = {
            'ndcg@5':      _ndcg(actual_grades, ideal_grades, 5),
            'ndcg@10':     _ndcg(actual_grades, ideal_grades, 10),
            'mrr@5':       _mrr(actual_grades, 5),
            'mrr@10':      _mrr(actual_grades, 10),
            'recall@10':   _recall_at_k(actual_grades, all_relevant_count, 10),
            'precision@5': _precision_at_k(actual_grades, 5),
            'map@10':      _average_precision(actual_grades, 10),
        }

    if skipped_no_judgments:
        logger.info(
            'Skipped %d queries with no relevance judgments (standard exclusion): %s',
            len(skipped_no_judgments), skipped_no_judgments,
        )

    if not per_query:
        return {m: 0.0 for m in TARGETS}

    # Average across queries
    metrics = {}
    for metric in TARGETS:
        values = [v[metric] for v in per_query.values()]
        metrics[metric] = sum(values) / len(values) if values else 0.0

    metrics['per_query'] = per_query
    metrics['num_queries_evaluated'] = len(per_query)
    metrics['num_queries_skipped_no_judgments'] = len(skipped_no_judgments)
    return metrics


# ---------------------------------------------------------------------------
# Build run from live search
# ---------------------------------------------------------------------------

def _build_run_from_search(golden_queries: list[dict]) -> dict:
    """Run all golden queries through the live search pipeline and collect results."""
    from evaluation.generate_judgments import _run_search

    run = {}
    for q in golden_queries:
        qid = q['id']
        query_text = q['query']
        try:
            results = _run_search(query_text, top_k=20)
        except Exception as e:
            logger.error(f"Search error for {qid}: {e}")
            run[qid] = {}
            continue

        # Assign inverse-rank scores (rank 1 = score 20, rank 20 = score 1)
        run[qid] = {}
        for rank, result in enumerate(results):
            rid = result.get('name', f'result_{rank}')
            run[qid][rid] = float(20 - rank)  # higher rank = higher score

    return run


# ---------------------------------------------------------------------------
# Main evaluate function
# ---------------------------------------------------------------------------

def evaluate(compare_to: str = None, save: bool = True) -> dict:
    """
    Full evaluation run.

    Args:
        compare_to: Path or filename (in results/) of previous eval JSON to compare against.
        save: Whether to save results JSON to disk.

    Returns:
        dict with metrics + optional delta.
    """
    # Load judgments
    if not JUDGMENTS_PATH.exists():
        raise FileNotFoundError(
            f"golden_judgments.json not found at {JUDGMENTS_PATH}. "
            "Run generate_judgments.py first."
        )

    with open(JUDGMENTS_PATH, 'r') as f:
        judgment_data = json.load(f)

    # Build qrels: {qid: {result_id: score}}
    raw_judgments = judgment_data.get('judgments', {})
    qrels = {}
    for qid, results in raw_judgments.items():
        qrels[qid] = {rid: float(info['score']) for rid, info in results.items()}

    # Load golden queries to get the full list
    with open(GOLDEN_QUERIES_PATH, 'r') as f:
        golden_data = json.load(f)
    golden_queries = golden_data['queries']

    # Build run from live search
    logger.info("Running all golden queries through search pipeline...")
    run = _build_run_from_search(golden_queries)

    # Compute metrics
    logger.info("Computing metrics...")
    metrics = compute_metrics(qrels, run)

    # Pretty print
    _print_metrics_table(metrics)

    # Compare to baseline
    delta = None
    if compare_to:
        delta = _compare_to_baseline(metrics, compare_to)
        _print_delta_table(delta)

    # Check regression
    passed_gate = True
    if compare_to and delta:
        ndcg10_drop = delta.get('ndcg@10', 0)
        if ndcg10_drop < -REGRESSION_THRESHOLD:
            logger.error(
                f"REGRESSION DETECTED: NDCG@10 dropped {abs(ndcg10_drop):.4f} "
                f"(threshold: {REGRESSION_THRESHOLD})"
            )
            passed_gate = False

    # Check targets
    logger.info("\nTarget check:")
    all_passed = True
    for metric, target in TARGETS.items():
        val = metrics.get(metric, 0.0)
        status = 'PASS' if val >= target else 'FAIL'
        if status == 'FAIL':
            all_passed = False
        logger.info(f"  {metric:15s}: {val:.4f} (target {target:.2f}) [{status}]")

    # Save results
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    output = {
        'timestamp': timestamp,
        'metrics': {k: v for k, v in metrics.items() if k != 'per_query'},
        'per_query': metrics.get('per_query', {}),
        'num_queries': metrics.get('num_queries_evaluated', 0),
        'targets_passed': all_passed,
        'regression_guard_passed': passed_gate,
        'delta_vs_baseline': delta,
    }

    if save:
        RESULTS_DIR.mkdir(exist_ok=True)
        out_path = RESULTS_DIR / f'eval_{timestamp}.json'
        with open(out_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        logger.info(f"\nResults saved to: {out_path}")

    return output


def _print_metrics_table(metrics: dict):
    logger.info("\n" + "=" * 55)
    logger.info(f"{'Metric':<20} {'Value':>10}")
    logger.info("=" * 55)
    for metric in TARGETS:
        val = metrics.get(metric, 0.0)
        logger.info(f"  {metric:<18} {val:>10.4f}")
    logger.info("=" * 55)
    logger.info(f"  Queries evaluated: {metrics.get('num_queries_evaluated', 0)}")


def _compare_to_baseline(current: dict, baseline_path: str) -> dict:
    """Load a previous eval file and compute deltas."""
    path = Path(baseline_path)
    if not path.is_absolute():
        path = RESULTS_DIR / baseline_path

    if not path.exists():
        logger.warning(f"Baseline file not found: {path}")
        return {}

    with open(path, 'r') as f:
        baseline = json.load(f)

    baseline_metrics = baseline.get('metrics', {})
    delta = {}
    for metric in TARGETS:
        cur = current.get(metric, 0.0)
        base = baseline_metrics.get(metric, 0.0)
        delta[metric] = cur - base

    return delta


def _print_delta_table(delta: dict):
    logger.info("\n" + "=" * 55)
    logger.info(f"{'Metric':<20} {'Delta':>10}")
    logger.info("=" * 55)
    for metric, d in delta.items():
        sign = '+' if d >= 0 else ''
        logger.info(f"  {metric:<18} {sign}{d:>9.4f}")
    logger.info("=" * 55)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Evaluate Zarailink search quality')
    parser.add_argument('--compare-to', type=str, default=None,
                        help='Previous eval JSON file to compare against (for delta + regression guard)')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to disk')
    args = parser.parse_args()

    _setup_django()
    result = evaluate(compare_to=args.compare_to, save=not args.no_save)

    if not result.get('regression_guard_passed', True):
        sys.exit(1)


if __name__ == '__main__':
    main()
