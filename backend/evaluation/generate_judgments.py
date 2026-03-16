"""
backend/evaluation/generate_judgments.py

Generates relevance judgments for the golden query set.

Supports two judge modes:
  1. GPT-4o-mini (requires OPENAI_KEY env var)
  2. Heuristic fallback (deterministic, no API needed)

Usage:
    python manage.py shell -c "
    import django
    import sys
    sys.path.insert(0, '.')
    from evaluation.generate_judgments import run
    run()
    "
    OR directly:
    cd backend && python evaluation/generate_judgments.py
"""

import os
import sys
import json
import time
import django
import logging
import re
from pathlib import Path
from datetime import datetime

# --- Django setup (when run as a standalone script) ---
def _setup_django():
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(backend_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    django.setup()

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    _setup_django()

BASE_DIR = Path(__file__).resolve().parent
GOLDEN_QUERIES_PATH = BASE_DIR / 'golden_queries.json'
JUDGE_PROMPT_PATH = BASE_DIR / 'judge_prompt.txt'
OUTPUT_PATH = BASE_DIR / 'golden_judgments.json'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


# ---------------------------------------------------------------------------
# Search pipeline caller
# ---------------------------------------------------------------------------

def _run_search(query: str, top_k: int = 20) -> list[dict]:
    """Run the search pipeline and return up to top_k results."""
    from search.services.query_parser import QueryInterpreter
    from search.services.nlp import QueryMatcher
    from search.services.aggregation import SupplierAggregator
    from search.services.ranking_ltr import RankingEnsemble

    interpreter = QueryInterpreter()
    parsed = interpreter.parse(query)

    # Multi-intent: collect all sub-intent results
    if parsed.get('multi_intent') and parsed.get('sub_intents'):
        all_results = []
        seen = set()
        for sub in parsed['sub_intents']:
            sub_results = _run_single_intent(sub, query)
            for r in sub_results:
                key = r.get('name', '')
                if key and key not in seen:
                    seen.add(key)
                    all_results.append(r)
        return all_results[:top_k]

    return _run_single_intent(parsed, query, top_k)


def _run_single_intent(parsed: dict, raw_query: str, top_k: int = 20) -> list[dict]:
    from search.services.nlp import QueryMatcher
    from search.services.aggregation import SupplierAggregator
    from search.services.ranking_ltr import RankingEnsemble

    product_term = parsed.get('product') or ''
    f8_no_product = (
        parsed.get('family') == 8
        and bool(parsed.get('counterparty_name'))
        and not product_term
    )
    nlp_term = '' if f8_no_product else (product_term or raw_query)

    matched_subcategories = []
    if nlp_term.strip():
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(nlp_term)

    country_filter = parsed.get('country_filter', [])
    price_filter = {}
    if parsed.get('price_ceiling'):
        price_filter['ceiling'] = parsed['price_ceiling']
    if parsed.get('price_floor'):
        price_filter['floor'] = parsed['price_floor']

    has_filters = bool(country_filter or price_filter or parsed.get('volume_mt'))

    is_f8_with_buyer = parsed.get('family') == 8 and bool(parsed.get('counterparty_name'))

    if not matched_subcategories and not has_filters and not is_f8_with_buyer:
        return []

    subcategory_ids = None
    if matched_subcategories:
        top = matched_subcategories[0]
        if top['score'] > 0.95:
            threshold = top['score'] - 0.05
            subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
        else:
            subcategory_ids = [m['id'] for m in matched_subcategories]

    # Time range
    time_filter = None
    time_range_str = parsed.get('time_range')
    if time_range_str:
        time_filter = _parse_time_range(time_range_str)

    aggregator = SupplierAggregator()
    results = aggregator.get_suppliers_for_subcategories(
        subcategory_ids,
        intent=parsed.get('intent', 'BUY'),
        scope=parsed.get('scope', 'WORLDWIDE'),
        country_filter=country_filter,
        price_filter=price_filter if price_filter else None,
        volume_filter=parsed.get('volume_mt'),
        time_filter=time_filter,
    )

    ranker = RankingEnsemble()
    ranked = ranker.rank_candidates(results, parsed)

    # Enrich results with matched product names for judge context
    matched_product_names = [m.get('name', '') for m in matched_subcategories[:3]] if matched_subcategories else []
    product_context = ', '.join(filter(None, matched_product_names)) or (product_term or '')
    for r in ranked:
        if 'products' not in r:
            r['products'] = product_context

    return ranked[:top_k]


def _parse_time_range(s: str):
    """Minimal time range parser for eval — just delegates to views logic."""
    try:
        from search.views import SearchViewSet
        v = SearchViewSet()
        return v._parse_time_range(s)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Judge: heuristic fallback
# ---------------------------------------------------------------------------

_PRODUCT_KEYWORDS = {
    'dextrose': ['dextrose', 'glucose'],
    'lactose': ['lactose', 'lacto'],
    'sugar': ['sugar', 'sucrose', 'refined sugar'],
    'maltodextrin': ['maltodextrin', 'malto'],
    'caramel': ['caramel', 'caramel color'],
    'fructose': ['fructose'],
    'candy': ['candy', 'mentos', 'fruittella'],
    'chocolate': ['chocolate'],
}


def _heuristic_judge(query: str, result: dict) -> tuple[int, str]:
    """
    Assign a relevance score 0–3 using deterministic heuristics.
    Returns (score, reasoning).
    """
    query_l = query.lower()
    name = (result.get('name') or '').lower()
    country = (result.get('country') or '').lower()
    total_vol = float(result.get('total_volume') or 0)
    shipments = int(result.get('shipment_count') or 0)
    avg_price = float(result.get('avg_price') or 0)
    products = (result.get('products') or '').lower()

    # --- F8: company name in query ---
    # Require ≥3 tokens to avoid triggering on product-keyword coincidences
    # (e.g. "Dextrose Co" matching query "dextrose suppliers")
    company_tokens = [t for t in name.split() if len(t) > 3]
    query_tokens = query_l.split()
    exact_match_score = sum(1 for t in company_tokens if t in query_tokens)
    if exact_match_score >= 3:
        return 3, "Company name matches query directly."
    if exact_match_score == 2:
        return 2, "Partial company name match."

    # --- Product relevance ---
    product_match = False
    matched_product_name = ''
    for prod, keywords in _PRODUCT_KEYWORDS.items():
        if any(kw in query_l for kw in keywords):
            if any(kw in name or kw in products for kw in keywords):
                product_match = True
                matched_product_name = prod
                break

    if not product_match:
        # Check if query product appears anywhere in the result
        query_words = set(re.findall(r'\b\w{4,}\b', query_l))
        name_words = set(re.findall(r'\b\w{4,}\b', name + ' ' + products))
        overlap = query_words & name_words
        if overlap:
            product_match = True
            matched_product_name = ', '.join(overlap)

    if not product_match:
        return 0, "Product in query does not match result's traded goods."

    # --- Country filter ---
    country_in_query = False
    country_match = True
    for country_name in ['china', 'germany', 'turkey', 'united states', 'usa', 'uae', 'indonesia',
                          'bahrain', 'malaysia', 'netherlands', 'france', 'italy', 'thailand',
                          'united kingdom', 'new zealand', 'vietnam']:
        if country_name in query_l:
            country_in_query = True
            if country_name not in country and not (country_name == 'usa' and 'united states' in country):
                country_match = False
            break

    if country_in_query and not country_match:
        return 0, f"Country filter in query does not match result country '{result.get('country')}'."

    # --- Volume / shipment credibility ---
    if shipments == 0 or total_vol == 0:
        return 1, "Product match but supplier has zero volume/shipments."

    # --- Price filter ---
    price_ceiling = None
    price_floor = None
    price_match = re.search(r'under\s+\$?([\d,]+)', query_l)
    if price_match:
        price_ceiling = float(price_match.group(1).replace(',', ''))
    price_match_floor = re.search(r'above\s+\$?([\d,]+)', query_l)
    if price_match_floor:
        price_floor = float(price_match_floor.group(1).replace(',', ''))

    if price_ceiling and avg_price > 0 and avg_price > price_ceiling * 1.5:
        return 1, f"Product matches but avg price {avg_price:.0f}/MT exceeds ceiling {price_ceiling}/MT."
    if price_floor and avg_price > 0 and avg_price < price_floor * 0.5:
        return 1, f"Product matches but avg price {avg_price:.0f}/MT is well below floor {price_floor}/MT."

    # --- Score based on credibility ---
    if shipments >= 10 and total_vol >= 100:
        score = 3
        reasoning = f"Strong product match ({matched_product_name}), high volume supplier ({total_vol:.0f} MT, {shipments} shipments)."
    elif shipments >= 3 or total_vol >= 20:
        score = 2
        reasoning = f"Good product match ({matched_product_name}), moderate activity ({total_vol:.0f} MT, {shipments} shipments)."
    else:
        score = 1
        reasoning = f"Product matches ({matched_product_name}) but supplier has limited activity ({shipments} shipments)."

    return score, reasoning


# ---------------------------------------------------------------------------
# Judge: GPT-4o-mini
# ---------------------------------------------------------------------------

def _gpt_judge(query: str, result: dict, prompt_template: str, client, retries: int = 3) -> tuple[int, str]:
    """Call GPT-4o-mini to judge relevance. Returns (score, reasoning)."""
    prompt = prompt_template.format(
        query=query,
        company_name=result.get('name', 'Unknown'),
        country=result.get('country', 'Unknown'),
        total_volume_mt=f"{result.get('total_volume', 0):.1f}",
        shipment_count=result.get('shipment_count', 0),
        avg_price_usd_mt=f"{result.get('avg_price', 0):.2f}",
        last_shipment_date=str(result.get('last_shipment_date', 'N/A')),
        products=result.get('products', result.get('name', 'N/A')),
    )

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0,
                max_tokens=150,
            )
            text = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            data = json.loads(text)
            score = int(data.get('relevance_score', 0))
            reasoning = data.get('reasoning', '')
            return max(0, min(3, score)), reasoning
        except json.JSONDecodeError as e:
            logger.warning(f"GPT returned invalid JSON (attempt {attempt+1}): {e}")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"GPT API error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)

    logger.warning(f"GPT judge failed after {retries} retries for query='{query}'. Falling back to heuristic.")
    return _heuristic_judge(query, result)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(use_gpt: bool = None, max_queries: int = None):
    """
    Generate relevance judgments for all golden queries.

    Args:
        use_gpt: Force GPT mode (True) or heuristic mode (False).
                 Default: auto-detect based on OPENAI_KEY env var.
        max_queries: Limit to first N queries (for testing).
    """
    # Load golden queries
    with open(GOLDEN_QUERIES_PATH, 'r') as f:
        golden = json.load(f)
    queries = golden['queries']
    if max_queries:
        queries = queries[:max_queries]

    # Detect judge mode
    api_key = os.environ.get('OPENAI_KEY') or os.environ.get('OPENAI_API_KEY')
    if use_gpt is None:
        use_gpt = bool(api_key)

    gpt_client = None
    prompt_template = None
    if use_gpt:
        try:
            import openai
            gpt_client = openai.OpenAI(api_key=api_key)
            with open(JUDGE_PROMPT_PATH, 'r') as f:
                prompt_template = f.read()
            logger.info("Judge mode: GPT-4o-mini")
        except ImportError:
            logger.warning("openai package not installed. Falling back to heuristic judge.")
            use_gpt = False
    if not use_gpt:
        logger.info("Judge mode: heuristic fallback")

    judgments = {}
    total_pairs = 0
    skipped = 0
    cost_estimate_usd = 0.0  # ~$0.15 per 1M input tokens for gpt-4o-mini

    for i, q in enumerate(queries):
        qid = q['id']
        query_text = q['query']
        logger.info(f"[{i+1}/{len(queries)}] Running query: {qid} — '{query_text}'")

        try:
            results = _run_search(query_text, top_k=20)
        except Exception as e:
            logger.error(f"Search failed for {qid}: {e}")
            skipped += 1
            continue

        if not results:
            logger.warning(f"  → 0 results returned for {qid}")
            judgments[qid] = {}
            continue

        logger.info(f"  → {len(results)} results returned")
        judgments[qid] = {}

        for rank, result in enumerate(results):
            result_id = result.get('name', f'result_{rank}')

            if use_gpt and gpt_client:
                score, reasoning = _gpt_judge(query_text, result, prompt_template, gpt_client)
                # Rough cost: ~300 tokens per call, gpt-4o-mini $0.15/1M input
                cost_estimate_usd += 300 * 0.15 / 1_000_000
            else:
                score, reasoning = _heuristic_judge(query_text, result)

            judgments[qid][result_id] = {
                'score': score,
                'reasoning': reasoning,
                'rank': rank + 1,
                'country': result.get('country', ''),
                'total_volume': result.get('total_volume', 0),
                'shipment_count': result.get('shipment_count', 0),
            }
            total_pairs += 1

    # Save output
    output = {
        'version': '1.0',
        'generated_at': datetime.now().isoformat(),
        'judge_mode': 'gpt-4o-mini' if use_gpt else 'heuristic',
        'total_queries': len(queries),
        'total_pairs': total_pairs,
        'skipped_queries': skipped,
        'judgments': judgments,
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"\n{'='*60}")
    logger.info(f"Done. {total_pairs} (query, result) pairs judged.")
    logger.info(f"Skipped queries: {skipped}")
    if use_gpt:
        logger.info(f"Estimated GPT cost: ${cost_estimate_usd:.4f} USD")
    logger.info(f"Output saved to: {OUTPUT_PATH}")

    return output


if __name__ == '__main__':
    _setup_django()
    run()
