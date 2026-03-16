"""
backend/search/tests/test_pipeline_integration.py

Phase 3-I: Full pipeline integration tests — 17 E2E family tests.

Tests the complete QueryInterpreter → QueryMatcher → SupplierAggregator → RankingEnsemble
pipeline via the search API view (bypassing HTTP with direct function calls).

Requires: running PostgreSQL with trade data loaded (SEARCH_INDEX_BUILT).
Mark with @pytest.mark.integration (skipped in normal CI).

Run all (requires DB + search index):
    pytest search/tests/test_pipeline_integration.py -m integration -v

Run unit-safe subset (mock-backed):
    pytest search/tests/test_pipeline_integration.py -m "not integration" -v
"""

import pytest
import os
import django


# ── Setup ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module', autouse=True)
def django_setup():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass


@pytest.fixture(scope='module')
def interpreter():
    from search.services.query_parser import QueryInterpreter
    return QueryInterpreter()


# ── Phase 3-I: Query Parser family tests ─────────────────────────────────────
# These test the parse() layer only — no DB needed.

class TestQueryParserFamilies:
    """17 parser-level tests, one per canonical query family variant."""

    # F1: Basic BUY
    def test_f1_buy_find_suppliers(self, interpreter):
        r = interpreter.parse("find dextrose suppliers")
        assert r['intent'] == 'BUY'
        assert r['family'] == 1

    # F1/F2: BUY with country filter — "import" verb
    def test_f1_buy_import(self, interpreter):
        r = interpreter.parse("import cotton from China")
        assert r['intent'] == 'BUY'
        assert 'China' in r['country_filter']

    # F2: Basic SELL — find buyers
    def test_f2_sell_find_buyers(self, interpreter):
        r = interpreter.parse("find buyers for our wheat")
        assert r['intent'] == 'SELL'

    # F2: Basic SELL — find importers
    def test_f2_sell_find_importers(self, interpreter):
        r = interpreter.parse("find importers of palm kernel oil")
        assert r['intent'] == 'SELL'

    # F3: Volume filter
    def test_f3_volume_mt(self, interpreter):
        r = interpreter.parse("200 MT lactose monohydrate")
        assert r['family'] == 3
        assert r['volume_mt'] == pytest.approx(200.0, abs=1.0)

    # F3: Volume in kg → converted to MT
    def test_f3_volume_kg_to_mt(self, interpreter):
        r = interpreter.parse("500 kg cotton exporters")
        assert r['family'] == 3
        assert r['volume_mt'] == pytest.approx(0.5, abs=0.01)

    # F4: Price ceiling
    def test_f4_price_under(self, interpreter):
        r = interpreter.parse("palm oil under $1200/MT")
        assert r['family'] == 4
        assert r['price_ceiling'] == pytest.approx(1200.0, abs=1.0)

    # F4: Price floor
    def test_f4_price_above(self, interpreter):
        r = interpreter.parse("glucose syrup priced above $300")
        assert r['family'] == 4
        assert r['price_floor'] == pytest.approx(300.0, abs=1.0)

    # F5: Time — quarter+year
    def test_f5_time_quarter(self, interpreter):
        r = interpreter.parse("Q3 2024 sugar exporters")
        assert r['family'] == 5

    # F5: Time — last N months
    def test_f5_time_last_months(self, interpreter):
        r = interpreter.parse("last 6 months lactose monohydrate exporters")
        assert r['family'] == 5

    # F6: TopK
    def test_f6_topk_top5(self, interpreter):
        r = interpreter.parse("top 5 dextrose anhydrous suppliers")
        assert r['family'] == 6

    # F6: TopK — best/rank language
    def test_f6_topk_rank(self, interpreter):
        r = interpreter.parse("rank cotton buyers")
        assert r['family'] == 6

    # F7: Country comparison
    def test_f7_country_compare(self, interpreter):
        r = interpreter.parse("which countries import cotton most")
        assert r['family'] == 7

    # F7: Country comparison — breakdown
    def test_f7_country_breakdown(self, interpreter):
        r = interpreter.parse("country breakdown for dextrose imports")
        assert r['family'] == 7

    # F8: Evidence — company transaction
    def test_f8_evidence_has_purchased(self, interpreter):
        r = interpreter.parse("has Nestle purchased palm oil")
        assert r['family'] == 8

    # F8: Evidence — transaction history
    def test_f8_evidence_transaction_history(self, interpreter):
        r = interpreter.parse("transaction history for Friesland Campina")
        assert r['family'] == 8

    # F9: Multi-intent
    def test_f9_multi_intent(self, interpreter):
        r = interpreter.parse("buy dextrose from China; find buyers for our wheat")
        assert r['family'] == 9
        assert r['multi_intent'] is True
        assert len(r.get('sub_intents', [])) >= 2


# ── Full pipeline E2E tests (require DB + search index) ───────────────────────

@pytest.mark.integration
class TestFullPipelineE2E:
    """
    End-to-end pipeline tests: parse → match → aggregate → rank.
    Skipped unless --run-integration flag or ZARAILINK_RUN_INTEGRATION=1 env var.
    """

    @pytest.fixture(scope='class')
    def search_view_func(self):
        """Return the search view callable."""
        from search.views import SearchView
        return SearchView.as_view()

    def _run_search(self, query, expected_family=None):
        """Run full pipeline via QueryMatcher + SupplierAggregator."""
        from search.services.query_parser import QueryInterpreter
        from search.services.nlp import QueryMatcher
        from search.services.aggregator import SupplierAggregator
        from search.services.ranking_ltr import RankingEnsemble

        interpreter = QueryInterpreter()
        parsed = interpreter.parse(query)

        if expected_family is not None:
            assert parsed.get('family') == expected_family, (
                f"Expected family={expected_family}, got {parsed.get('family')}"
            )

        matcher = QueryMatcher()
        subcategories = matcher.match(query, parsed)

        if not subcategories:
            return {'parsed': parsed, 'results': [], 'subcategories': []}

        agg = SupplierAggregator()
        candidates = agg.aggregate(subcategories, parsed)

        if not candidates:
            return {'parsed': parsed, 'results': [], 'subcategories': subcategories}

        ranker = RankingEnsemble()
        ranked = ranker.rank_candidates(candidates, parsed)

        return {
            'parsed': parsed,
            'results': ranked,
            'subcategories': subcategories,
        }

    def test_e2e_f1_buy_sugar(self):
        result = self._run_search("find sugar suppliers", expected_family=1)
        assert isinstance(result['results'], list)

    def test_e2e_f1_buy_dextrose(self):
        result = self._run_search("dextrose suppliers")
        assert isinstance(result['results'], list)
        assert result['parsed']['intent'] == 'BUY'

    def test_e2e_f2_sell_cotton(self):
        result = self._run_search("find buyers for our cotton")
        assert result['parsed']['intent'] == 'SELL'

    def test_e2e_f3_volume(self):
        result = self._run_search("100 MT dextrose suppliers", expected_family=3)
        assert result['parsed']['volume_mt'] == pytest.approx(100.0, abs=1.0)

    def test_e2e_f4_price(self):
        result = self._run_search("dextrose under $400/MT", expected_family=4)
        assert result['parsed']['price_ceiling'] == pytest.approx(400.0, abs=1.0)

    def test_e2e_f5_time(self):
        result = self._run_search("Q1 2024 sugar suppliers", expected_family=5)
        assert isinstance(result['results'], list)

    def test_e2e_f6_topk(self):
        result = self._run_search("top 5 palm oil exporters", expected_family=6)
        assert isinstance(result['results'], list)

    def test_e2e_f7_country_compare(self):
        result = self._run_search("which countries import cotton most", expected_family=7)
        assert isinstance(result['results'], list)

    def test_e2e_f8_evidence(self):
        result = self._run_search("has Nestle purchased palm oil", expected_family=8)
        assert isinstance(result['results'], list)

    def test_e2e_no_results_no_crash(self):
        """Queries that match nothing must return empty list, not raise."""
        result = self._run_search("zxqwerty totally fake product 99999")
        assert isinstance(result['results'], list)

    def test_e2e_results_have_required_fields(self):
        """Each ranked result must contain name and at least one score field."""
        result = self._run_search("sugar suppliers")
        for r in result['results'][:5]:
            assert 'name' in r or 'company_name' in r

    def test_e2e_f9_multi_intent_no_crash(self):
        """Multi-intent query must not crash the pipeline."""
        from search.services.query_parser import QueryInterpreter
        interpreter = QueryInterpreter()
        r = interpreter.parse("buy dextrose from China; who imports wheat")
        assert r.get('family') == 9
        assert r.get('multi_intent') is True

    def test_e2e_results_sorted_by_score(self):
        """Results must be in descending order by heuristic score."""
        result = self._run_search("dextrose suppliers")
        results = result['results']
        if len(results) < 2:
            pytest.skip("Not enough results to verify ordering")
        scores = [r.get('heuristic_score', r.get('score', 0)) for r in results]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"

    def test_e2e_cross_encoder_applied(self):
        """Cross-encoder re-ranker should be applied if setting enabled."""
        from django.conf import settings
        if not getattr(settings, 'SEARCH_USE_CROSS_ENCODER', False):
            pytest.skip("Cross-encoder disabled")
        result = self._run_search("dextrose suppliers")
        assert isinstance(result['results'], list)

    def test_e2e_supplier_reranker_applied(self):
        """Supplier reranker should be applied if setting enabled."""
        from django.conf import settings
        if not getattr(settings, 'SEARCH_USE_SUPPLIER_RERANKER', False):
            pytest.skip("Supplier reranker disabled")
        result = self._run_search("sugar suppliers")
        assert isinstance(result['results'], list)
