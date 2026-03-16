"""
backend/evaluation/benchmark_latency.py

Measures per-stage and end-to-end search pipeline latency.

Outputs: P50, P75, P95, P99 in ms.
Per-stage breakdown: parse, match, aggregate, rank.

Usage:
    cd backend && python evaluation/benchmark_latency.py
    cd backend && python evaluation/benchmark_latency.py --queries 50
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BASE_DIR = Path(__file__).resolve().parent
GOLDEN_QUERIES_PATH = BASE_DIR / 'golden_queries.json'
RESULTS_DIR = BASE_DIR / 'results'


def _setup_django():
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    import django
    django.setup()


def _percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * p / 100
    f = int(k)
    c = f + 1
    if c >= len(data_sorted):
        return data_sorted[-1]
    return data_sorted[f] + (data_sorted[c] - data_sorted[f]) * (k - f)


def run_benchmark(n_queries: int = 50) -> dict:
    """
    Run n_queries through the full pipeline with per-stage timing.
    """
    from search.services.query_parser import QueryInterpreter
    from search.services.nlp import QueryMatcher
    from search.services.aggregation import SupplierAggregator
    from search.services.ranking_ltr import RankingEnsemble

    with open(GOLDEN_QUERIES_PATH, 'r') as f:
        golden = json.load(f)

    all_queries = [q['query'] for q in golden['queries']]
    # Sample with replacement to reach n_queries
    if len(all_queries) >= n_queries:
        queries = random.sample(all_queries, n_queries)
    else:
        queries = all_queries * (n_queries // len(all_queries) + 1)
        queries = queries[:n_queries]

    timings = {
        'total_ms': [],
        'parse_ms': [],
        'match_ms': [],
        'agg_ms': [],
        'rank_ms': [],
    }

    # Warm up singletons
    logger.info("Warming up pipeline singletons...")
    try:
        QueryMatcher()
        QueryInterpreter()
    except Exception:
        pass

    logger.info(f"Benchmarking {n_queries} queries...")

    for i, query_text in enumerate(queries):
        t0 = time.perf_counter()

        # Stage 1: Parse
        t_parse_start = time.perf_counter()
        interpreter = QueryInterpreter()
        parsed = interpreter.parse(query_text)
        t_parse_end = time.perf_counter()

        product_term = parsed.get('product') or ''
        f8_no_product = (
            parsed.get('family') == 8
            and bool(parsed.get('counterparty_name'))
            and not product_term
        )
        nlp_term = '' if f8_no_product else (product_term or query_text)

        # Stage 2: Match
        t_match_start = time.perf_counter()
        matched = []
        if nlp_term.strip():
            matcher = QueryMatcher()
            matched = matcher.match(nlp_term)
        t_match_end = time.perf_counter()

        # Stage 3: Aggregate
        t_agg_start = time.perf_counter()
        subcategory_ids = None
        if matched:
            top = matched[0]
            threshold = top['score'] - 0.05 if top['score'] > 0.95 else 0
            subcategory_ids = [m['id'] for m in matched if m['score'] >= threshold]

        aggregator = SupplierAggregator()
        results = aggregator.get_suppliers_for_subcategories(subcategory_ids) if subcategory_ids else []
        t_agg_end = time.perf_counter()

        # Stage 4: Rank
        t_rank_start = time.perf_counter()
        if results:
            ranker = RankingEnsemble()
            ranker.rank_candidates(results, parsed)
        t_rank_end = time.perf_counter()

        t_total_end = time.perf_counter()

        timings['total_ms'].append((t_total_end - t0) * 1000)
        timings['parse_ms'].append((t_parse_end - t_parse_start) * 1000)
        timings['match_ms'].append((t_match_end - t_match_start) * 1000)
        timings['agg_ms'].append((t_agg_end - t_agg_start) * 1000)
        timings['rank_ms'].append((t_rank_end - t_rank_start) * 1000)

        if (i + 1) % 10 == 0:
            logger.info(f"  {i+1}/{n_queries} queries complete")

    # Compute percentiles
    results_out = {}
    for stage, times in timings.items():
        results_out[stage] = {
            'p50': round(_percentile(times, 50), 2),
            'p75': round(_percentile(times, 75), 2),
            'p95': round(_percentile(times, 95), 2),
            'p99': round(_percentile(times, 99), 2),
            'mean': round(sum(times) / len(times), 2),
            'min': round(min(times), 2),
            'max': round(max(times), 2),
        }

    # Print results
    logger.info("\n" + "=" * 65)
    logger.info(f"{'Stage':<20} {'P50':>8} {'P75':>8} {'P95':>8} {'P99':>8} {'Mean':>8}")
    logger.info("=" * 65)
    for stage in ['total_ms', 'parse_ms', 'match_ms', 'agg_ms', 'rank_ms']:
        r = results_out[stage]
        logger.info(
            f"  {stage:<18} {r['p50']:>8.1f} {r['p75']:>8.1f} "
            f"{r['p95']:>8.1f} {r['p99']:>8.1f} {r['mean']:>8.1f}"
        )
    logger.info("=" * 65)
    logger.info("All values in ms.")

    # Check latency targets
    p95_total = results_out['total_ms']['p95']
    if p95_total <= 200:
        logger.info(f"✓ P95 latency {p95_total:.1f}ms is within 200ms target")
    else:
        logger.warning(f"✗ P95 latency {p95_total:.1f}ms EXCEEDS 200ms target")

    # Save
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    out_path = RESULTS_DIR / f'latency_{timestamp}.json'
    output = {
        'timestamp': timestamp,
        'n_queries': n_queries,
        'timings': results_out,
        'p95_target_ms': 200,
        'p95_passed': p95_total <= 200,
    }
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Results saved to: {out_path}")

    return output


def main():
    parser = argparse.ArgumentParser(description='Benchmark Zarailink search latency')
    parser.add_argument('--queries', type=int, default=50, help='Number of queries to run')
    args = parser.parse_args()

    _setup_django()
    run_benchmark(args.queries)


if __name__ == '__main__':
    main()
