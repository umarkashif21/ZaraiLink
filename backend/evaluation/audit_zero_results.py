"""
backend/evaluation/audit_zero_results.py

Phase 0-E: Zero-Result Rate Audit.

Runs all golden queries through the search pipeline and reports:
  - Which queries return zero results
  - Zero-result rate per family
  - Overall zero-result rate
  - Parsed query details for zero-result cases (to diagnose causes)

Target: < 5% zero-result rate overall after all pipeline phases.

Usage:
    cd backend
    python evaluation/audit_zero_results.py
    # or via management command:
    python manage.py evaluate_search --zero-results-audit
"""

import os
import sys
import json
import logging
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

GOLDEN_QUERIES_PATH = os.path.join(BACKEND_DIR, 'evaluation', 'golden_queries.json')
RESULTS_DIR = os.path.join(BACKEND_DIR, 'evaluation', 'results')


def _setup_django():
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass


def _run_query(query: str, family: str) -> dict:
    """
    Run a single query through the search pipeline.
    Returns dict with: results_count, parsed_query, matched_subcategories, error.
    """
    try:
        from search.services.query_parser import QueryInterpreter
        from search.services.nlp import QueryMatcher
        from search.services.aggregation import SupplierAggregator

        interpreter = QueryInterpreter()
        parsed = interpreter.parse(query)

        product_term = parsed.get('product') or ''
        f8_no_product = (
            parsed.get('family') == 8
            and bool(parsed.get('counterparty_name'))
            and not product_term
        )
        search_term = '' if f8_no_product else (product_term or query)

        matched = []
        if search_term.strip():
            matcher = QueryMatcher()
            matched = matcher.match(search_term)

        # Family 7 and 8 always return something if matched
        if parsed.get('family') in (7, 8):
            return {
                'results_count': 1 if matched or f8_no_product else 0,
                'parsed_query': parsed,
                'matched_subcategories': matched,
                'note': 'F7/F8 — result count approximated',
                'error': None,
            }

        if not matched:
            return {
                'results_count': 0,
                'parsed_query': parsed,
                'matched_subcategories': [],
                'error': None,
            }

        subcategory_ids = [m['id'] for m in matched]
        agg = SupplierAggregator()
        results = agg.get_suppliers_for_subcategories(
            subcategory_ids,
            intent=parsed.get('intent', 'BUY'),
            scope=parsed.get('scope', 'WORLDWIDE'),
            country_filter=parsed.get('country_filter', []),
            price_filter={
                k: v for k, v in {
                    'ceiling': parsed.get('price_ceiling'),
                    'floor': parsed.get('price_floor'),
                }.items() if v is not None
            },
            volume_filter=parsed.get('volume_mt'),
        )
        return {
            'results_count': len(results),
            'parsed_query': parsed,
            'matched_subcategories': matched,
            'error': None,
        }

    except Exception as e:
        logger.warning(f"Query failed: {query!r} — {e}")
        return {
            'results_count': -1,
            'parsed_query': {},
            'matched_subcategories': [],
            'error': str(e),
        }


def run_audit(save: bool = True) -> dict:
    """
    Run zero-result audit over all golden queries.
    Returns audit report dict.
    """
    _setup_django()

    with open(GOLDEN_QUERIES_PATH, encoding='utf-8') as f:
        golden = json.load(f)

    queries = golden['queries']
    logger.info(f"Auditing {len(queries)} golden queries for zero results...")

    zero_result_queries = []
    error_queries = []
    family_stats = {}

    for q in queries:
        qid = q['id']
        query_str = q['query']
        family = q['family']

        result = _run_query(query_str, family)

        if family not in family_stats:
            family_stats[family] = {'total': 0, 'zero': 0, 'error': 0}

        family_stats[family]['total'] += 1

        if result['error']:
            error_queries.append({
                'id': qid,
                'query': query_str,
                'family': family,
                'error': result['error'],
            })
            family_stats[family]['error'] += 1
        elif result['results_count'] == 0:
            zero_result_queries.append({
                'id': qid,
                'query': query_str,
                'family': family,
                'parsed_product': result['parsed_query'].get('product'),
                'parsed_intent': result['parsed_query'].get('intent'),
                'parsed_family': result['parsed_query'].get('family'),
                'matched_subcategories': len(result['matched_subcategories']),
            })
            family_stats[family]['zero'] += 1

        logger.info(
            f"  [{qid}] {query_str!r} → {result['results_count']} results"
            + (f" [ERROR: {result['error']}]" if result['error'] else "")
        )

    total = len(queries)
    total_zero = len(zero_result_queries)
    total_error = len(error_queries)
    zero_rate = total_zero / total if total > 0 else 0.0
    target_met = zero_rate < 0.05

    # Per-family zero rates
    family_zero_rates = {}
    for fam, stats in sorted(family_stats.items()):
        rate = stats['zero'] / stats['total'] if stats['total'] > 0 else 0.0
        family_zero_rates[fam] = {
            'total': stats['total'],
            'zero': stats['zero'],
            'error': stats['error'],
            'zero_rate': round(rate, 4),
        }

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_queries': total,
        'total_zero_results': total_zero,
        'total_errors': total_error,
        'zero_result_rate': round(zero_rate, 4),
        'target_met': target_met,
        'target': '< 5%',
        'family_breakdown': family_zero_rates,
        'zero_result_queries': zero_result_queries,
        'error_queries': error_queries,
    }

    # Print summary
    print("\n" + "=" * 60)
    print("ZERO-RESULT RATE AUDIT")
    print("=" * 60)
    print(f"Total queries:      {total}")
    print(f"Zero results:       {total_zero} ({zero_rate:.1%})")
    print(f"Errors:             {total_error}")
    print(f"Target (< 5%):      {'✓ PASSED' if target_met else '✗ FAILED'}")
    print()
    print(f"{'Family':<10} {'Total':>6} {'Zero':>6} {'Rate':>8}")
    print("-" * 35)
    for fam, stats in sorted(family_zero_rates.items()):
        flag = " ✗" if stats['zero_rate'] > 0.10 else ""
        print(f"{fam:<10} {stats['total']:>6} {stats['zero']:>6} {stats['zero_rate']:>7.1%}{flag}")

    if zero_result_queries:
        print(f"\nZero-result queries ({len(zero_result_queries)}):")
        for zq in zero_result_queries:
            print(f"  [{zq['id']}] {zq['query']!r}")
            print(f"    product={zq['parsed_product']!r}, family={zq['parsed_family']}, subcats={zq['matched_subcategories']}")

    if save:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
        out_path = os.path.join(RESULTS_DIR, f'zero_results_{ts}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"\nAudit report saved to {out_path}")

    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Zarailink zero-result rate audit')
    parser.add_argument('--no-save', action='store_true', help='Do not save report to disk')
    args = parser.parse_args()
    run_audit(save=not args.no_save)
