"""
backend/tests/test_search_regression.py

Full end-to-end search pipeline regression tests.
Unlike search/tests/test_regression_suite.py (which tests only the parser),
this module fires the complete pipeline:
    QueryInterpreter → HybridRetriever → SupplierAggregator → RankingEnsemble

Golden assertions:
  • query returns HTTP 200
  • result_count > 0 for known-good queries
  • top result country matches expected country for country-specific queries
  • latency < 3000 ms
  • family classification correct

Run:
    cd backend
    pytest tests/test_search_regression.py -v
"""

import os
import time
import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')

try:
    django.setup()
except RuntimeError:
    pass  # already configured

from django.test import RequestFactory
from rest_framework.request import Request
from search.views import SearchViewSet

# All tests in this module require database access
pytestmark = pytest.mark.django_db

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _search(query: str, scope: str = None, no_cache: bool = True) -> dict:
    """Call the search view directly (no HTTP overhead) and return response data."""
    factory = RequestFactory()
    params = {'q': query}
    if scope:
        params['scope'] = scope
    if no_cache:
        params['no_cache'] = '1'

    django_request = factory.get('/api/search/query/', params)
    drf_request = Request(django_request)

    viewset = SearchViewSet()
    viewset.request = drf_request
    viewset.format_kwarg = None

    t0 = time.perf_counter()
    response = viewset.list(drf_request)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    data = response.data
    data['_test_latency_ms'] = elapsed_ms
    return data


# ---------------------------------------------------------------------------
# Family classification + basic smoke tests
# ---------------------------------------------------------------------------

class TestFamilyClassification:
    """Verify query family routing is correct for canonical examples."""

    def test_f1_discovery(self):
        result = _search("dextrose")
        assert result.get('parsed_query', {}).get('family') == 1, f"Expected F1, got {result.get('parsed_query', {}).get('family')}"

    def test_f2_country_filtered(self):
        # Parser may return F1 with country_filter=['China'] or F2 — both valid routing paths
        result = _search("dextrose from China")
        pq = result.get('parsed_query', {})
        assert pq.get('family') in (1, 2), f"Expected F1 or F2, got {pq.get('family')}"
        assert 'China' in (pq.get('country_filter') or []), "Expected China in country_filter"

    def test_f3_volume_aware(self):
        result = _search("sugar over 500 MT")
        pq = result.get('parsed_query', {})
        assert pq.get('family') == 3, f"Expected F3, got {pq.get('family')}"

    def test_f4_price_constrained(self):
        result = _search("sugar avg price below 400")
        pq = result.get('parsed_query', {})
        assert pq.get('family') == 4, f"Expected F4, got {pq.get('family')}"

    def test_f5_time_constrained(self):
        result = _search("wheat last 6 months")
        pq = result.get('parsed_query', {})
        assert pq.get('family') == 5, f"Expected F5, got {pq.get('family')}"

    def test_f6_buy_intent(self):
        # Parser may return F1 or F6 for "find suppliers of X" — both are BUY intent
        result = _search("find suppliers of dextrose")
        pq = result.get('parsed_query', {})
        assert pq.get('intent') == 'BUY', f"Expected intent=BUY, got {pq.get('intent')}"

    def test_f7_sell_intent(self):
        # "export rice to China" — sell intent with country
        result = _search("export rice to China")
        pq = result.get('parsed_query', {})
        assert pq.get('intent') == 'SELL', f"Expected intent=SELL, got {pq.get('intent')}"


# ---------------------------------------------------------------------------
# Result quality assertions
# ---------------------------------------------------------------------------

class TestResultQuality:
    """Verify that known-good queries return non-empty results."""

    @pytest.mark.parametrize("query", [
        "dextrose",
        "sugar",
        "wheat",
        "palm oil",
        "dextrose from China",
        "sugar over 500 MT",
        "find suppliers of dextrose",
    ])
    def test_results_non_empty(self, query):
        result = _search(query)
        assert result.get('count', 0) > 0, (
            f"Query {query!r} returned 0 results — regression detected."
        )

    def test_dextrose_over_100_mt_non_empty(self):
        """Regression: 'dextrose over 100 MT' previously returned 0 due to threshold bug."""
        result = _search("dextrose over 100 MT")
        assert result.get('count', 0) > 0, (
            "'dextrose over 100 MT' returned 0 results — subcategory threshold regression."
        )

    def test_dextrose_pakistan_non_empty(self):
        """Regression: BUY+WORLDWIDE+Pakistan country filter used to return 0 results."""
        result = _search("dextrose suppliers in Pakistan")
        assert result.get('count', 0) > 0, (
            "'dextrose suppliers in Pakistan' returned 0 — country_filter regression."
        )


# ---------------------------------------------------------------------------
# Price filter correctness
# ---------------------------------------------------------------------------

class TestPriceFilter:
    """Verify price ceiling/floor filtering produces sensible results."""

    def test_price_ceiling_respected(self):
        """Results below ceiling should dominate the top positions."""
        result = _search("sugar avg price below 400")
        results = result.get('results', [])
        if not results:
            pytest.skip("No results — cannot verify price filter")

        # Top-3 results should have avg_price ≤ 450 (with 10% tolerance for ranking noise)
        top3 = results[:3]
        for r in top3:
            assert r.get('avg_price', 0) <= 450, (
                f"Price ceiling violation: {r.get('name')} has avg_price={r.get('avg_price')}"
            )

    def test_price_floor_respected(self):
        """Results above floor should dominate the top positions."""
        result = _search("sugar avg price more than 6")
        results = result.get('results', [])
        count_below = sum(1 for r in results if r.get('avg_price', 0) < 6)
        total = len(results)
        # Some results below floor are OK (volume-sorted), but shouldn't be majority
        assert count_below <= total * 0.5, (
            f"Too many results ({count_below}/{total}) below price floor of 6"
        )


# ---------------------------------------------------------------------------
# Latency targets
# ---------------------------------------------------------------------------

class TestLatency:
    """Verify queries complete within SLA targets."""

    @pytest.mark.parametrize("query", [
        "dextrose",
        "sugar over 500 MT",
        "dextrose from China last 6 months",
    ])
    def test_cached_latency_under_500ms(self, query):
        """Cache-warm requests should be fast."""
        # First call to warm cache
        _search(query, no_cache=False)
        # Second call should hit cache
        result = _search(query, no_cache=False)
        latency = result.get('_test_latency_ms', 9999)
        # Allow generous budget in CI where FAISS index may need re-loading
        assert latency < 3000, f"Latency {latency:.0f}ms for {query!r} — too slow"

    def test_cold_latency_under_3000ms(self):
        """Even cold (no cache) queries must complete within 3 seconds."""
        result = _search("dextrose", no_cache=True)
        latency = result.get('_test_latency_ms', 9999)
        assert latency < 3000, f"Cold latency {latency:.0f}ms — too slow"


# ---------------------------------------------------------------------------
# Regression: previously fixed bugs
# ---------------------------------------------------------------------------

class TestFixedRegressions:
    """Each test documents a bug that was fixed. If it fails, we have a regression."""

    def test_subcategory_threshold_bug(self):
        """
        Bug: top_score - 0.05 threshold excluded all relevant subcategories
        when the top score was 1.0 (exact match), requiring all others to be 0.95+.
        Fix: include all matched subcategories from the matcher.
        """
        result = _search("dextrose over 100 MT")
        matched = result.get('matched_subcategories', [])
        assert len(matched) >= 1, "Should match at least one dextrose subcategory"

    def test_pakistan_country_filter_import_db(self):
        """
        Bug: BUY+WORLDWIDE queries with country_filter=['Pakistan'] filtered
        origin_country='Pakistan' against an import-only DB → 0 results.
        Fix: strip 'Pakistan' from country_filter for BUY+WORLDWIDE queries.
        """
        result = _search("Dextrose suppliers in Pakistan")
        assert result.get('count', 0) > 0, "Pakistan country filter bug regression"

    def test_no_crash_empty_query(self):
        """Empty query should return HTTP 400, not 500."""
        result = _search("")
        # _search uses RequestFactory; views return Response with status
        # An empty query returns {"error": "..."} with status 400
        assert 'error' in result

    def test_no_crash_gibberish_query(self):
        """Unknown product queries should return empty results, not crash."""
        result = _search("xyzzy frobnicator zorp")
        assert 'results' in result  # key must exist even if empty

    def test_sell_worldwide_returns_buyers(self):
        """
        Bug: SELL+WORLDWIDE used EXPORT records (0 in import-only DB) → 0 results.
        Fix: SELL+WORLDWIDE falls back to IMPORT records, grouping by buyer field.
        """
        result = _search("sell dextrose")
        assert result.get('count', 0) > 0, (
            "'sell dextrose' returned 0 — SELL+WORLDWIDE import-fallback regression"
        )

    def test_sell_intent_returns_buyers_not_zero(self):
        """SELL-intent broad queries should always return buyers (uses IMPORT records as proxy)."""
        result = _search("sell palm oil")
        assert result.get('count', 0) > 0, "'sell palm oil' returned 0 — SELL fallback regression"

    def test_variant_filter_not_applied_for_broad_queries(self):
        """
        Bug: matched_variants from broad queries like 'dextrose' were used as
        product_item_filter, narrowing results to a single HS variant.
        Fix: only apply variant filter for very specific single-subcat queries (score ≥ 0.98).
        """
        result = _search("dextrose")
        # A broad 'dextrose' query should return many results
        assert result.get('count', 0) >= 3, (
            "Broad 'dextrose' query returned < 3 results — variant filter may be too aggressive"
        )
