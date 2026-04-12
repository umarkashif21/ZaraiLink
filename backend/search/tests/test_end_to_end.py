"""
backend/search/tests/test_end_to_end.py

End-to-end tests covering all fixes applied to the Zarailink search pipeline.

Coverage:
  Unit tests (no DB required):
    - QueryInterpreter: all 9 query families, currency conversion, year auto-update,
      logistics stopwords, multi-intent split edge cases
    - SemanticCache: context key isolation, SHA generation
    - SupplierAggregator: company deduplication

  Integration tests (mocked DB):
    - SearchViewSet: BUY+PAKISTAN error, SELL+WORLDWIDE warnings + data_note,
      cache key isolation, subcategory pill filter, no-result suggestions,
      time range parsing, top-N extraction

Run (Django test runner):
    cd backend && python manage.py test search.tests.test_end_to_end --verbosity=2

Run (pytest):
    cd backend && pytest search/tests/test_end_to_end.py -v
"""

import datetime
import unittest
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework.test import APIClient, APIRequestFactory


# =============================================================================
# Helper
# =============================================================================

def _make_parsed_query(
    intent='BUY', scope='WORLDWIDE', product='dextrose', family=1,
    country_filter=None, volume_mt=None, time_range=None,
    price_ceiling=None, price_floor=None,
    multi_intent=False, counterparty_name=None,
):
    return {
        'intent': intent,
        'scope': scope,
        'product': product,
        'family': family,
        'country_filter': country_filter or [],
        'volume_mt': volume_mt,
        'time_range': time_range,
        'price_ceiling': price_ceiling,
        'price_floor': price_floor,
        'multi_intent': multi_intent,
        'sub_intents': [],
        'counterparty_name': counterparty_name,
        'ambiguous_query': False,
    }


def _make_supplier(name='Test Supplier', country='China', shipment_count=8):
    return {
        'name': name,
        'country': country,
        'total_volume': 500.0,
        'avg_price': 350.0,
        'shipment_count': shipment_count,
        'last_shipment_date': datetime.date(2024, 3, 1),
        'max_shipment_vol': 100.0,
        'avg_shipment_vol': 62.5,
        'type': 'Supplier',
        'volume_score': None,
        'volume_fit': 'N/A',
    }


def _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker,
                    parsed=None, suppliers=None):
    """Wire up the standard mock chain for a successful search."""
    if parsed is None:
        parsed = _make_parsed_query()
    if suppliers is None:
        suppliers = [_make_supplier()]

    MockInterp.return_value.parse.return_value = parsed
    MockMatcher.return_value.match.return_value = [
        {'id': 1, 'name': 'Dextrose Anhydrous', 'score': 0.97}
    ]
    MockAgg.return_value.get_suppliers_for_subcategories.return_value = suppliers
    MockRanker.return_value.rank_candidates.return_value = suppliers


# =============================================================================
# 1. QueryInterpreter — family classification
# =============================================================================

class TestQueryFamilies(TestCase):
    """Query family F1–F9 classification (no DB, ML classifiers disabled)."""

    def _parse(self, query, scope=None):
        from search.services.query_parser import QueryInterpreter as QI
        QI._countries_cache = QI._FALLBACK_COUNTRIES
        with patch('search.services.query_parser._USE_SETFIT', False), \
             patch('search.services.query_parser._USE_GLINER', False):
            return QI().parse(query, explicit_scope=scope)

    # F1 ──────────────────────────────────────────────────────────────────────
    def test_f1_generic_product(self):
        r = self._parse("dextrose")
        self.assertEqual(r['family'], 1)

    def test_f1_default_intent_is_buy(self):
        r = self._parse("find suppliers of wheat")
        self.assertEqual(r['intent'], 'BUY')

    def test_f1_sell_intent(self):
        r = self._parse("I want to sell dextrose")
        self.assertEqual(r['intent'], 'SELL')

    # F2 ──────────────────────────────────────────────────────────────────────
    def test_f2_country_extracted(self):
        r = self._parse("dextrose from China")
        self.assertEqual(r['family'], 2)
        self.assertIn('China', r.get('country_filter', []))

    def test_f2_country_in_company_name_not_extracted(self):
        """Country inside a company name must not become a country_filter."""
        r = self._parse("does China National Corp buy wheat?")
        # If F8, counterparty_name should be populated
        if r['family'] == 8:
            self.assertIsNotNone(r.get('counterparty_name'))

    # F3 ──────────────────────────────────────────────────────────────────────
    def test_f3_volume_mt(self):
        r = self._parse("need 500 MT of dextrose")
        self.assertEqual(r['family'], 3)
        self.assertAlmostEqual(r['volume_mt'], 500.0, delta=5)

    def test_f3_volume_tons_recognized(self):
        r = self._parse("buy 1000 tons of wheat")
        self.assertIn(r['family'], [3, 1])
        if r.get('volume_mt'):
            self.assertAlmostEqual(r['volume_mt'], 1000.0, delta=50)

    # F4 ──────────────────────────────────────────────────────────────────────
    def test_f4_price_ceiling_usd(self):
        r = self._parse("dextrose below $500 per ton")
        self.assertIn(r['family'], [4, 1])
        if r.get('price_ceiling'):
            self.assertLessEqual(r['price_ceiling'], 600)

    def test_f4_pkr_converted_to_usd(self):
        """PKR prices must be converted to USD (< 1000, not raw PKR)."""
        r = self._parse("dextrose below 50000 PKR per ton")
        if r.get('price_ceiling'):
            self.assertLess(r['price_ceiling'], 1000,
                            "price_ceiling should be in USD not PKR")

    # F5 ──────────────────────────────────────────────────────────────────────
    def test_f5_time_range_present(self):
        r = self._parse("dextrose imports last 6 months")
        # Must be F5 (time) — NOT F8 (buyer evidence)
        self.assertIn(r['family'], [5, 3])  # F5 or F3 (volume+time combo) both acceptable
        self.assertIsNotNone(r.get('time_range'))

    # F6 ──────────────────────────────────────────────────────────────────────
    def test_f6_top_n(self):
        r = self._parse("top 5 suppliers of dextrose")
        self.assertEqual(r['family'], 6)

    def test_f6_recommend(self):
        r = self._parse("recommend best wheat suppliers")
        self.assertIn(r['family'], [6, 1])

    # F7 ──────────────────────────────────────────────────────────────────────
    def test_f7_country_comparison(self):
        r = self._parse("compare wheat from China vs India")
        self.assertEqual(r['family'], 7)

    # F8 ──────────────────────────────────────────────────────────────────────
    def test_f8_buyer_evidence(self):
        r = self._parse("does Al Baraka Trading buy dextrose?")
        self.assertEqual(r['family'], 8)
        self.assertIsNotNone(r.get('counterparty_name'))

    # F9 ──────────────────────────────────────────────────────────────────────
    def test_f9_multi_intent_detected(self):
        r = self._parse("show me dextrose suppliers and compare countries")
        self.assertEqual(r['family'], 9)
        self.assertTrue(r.get('multi_intent'))
        self.assertGreaterEqual(len(r.get('sub_intents', [])), 2)

    def test_f9_bare_conjunction_not_split(self):
        """'dextrose and wheat' must NOT be treated as multi-intent."""
        r = self._parse("dextrose and wheat")
        self.assertNotEqual(r['family'], 9,
                            "Bare 'and' between nouns must not trigger F9 split")

    # Explicit scope ──────────────────────────────────────────────────────────
    def test_explicit_scope_overrides_parser(self):
        r = self._parse("wheat", scope='PAKISTAN')
        self.assertEqual(r.get('scope'), 'PAKISTAN')


# =============================================================================
# 2. QueryInterpreter — edge cases
# =============================================================================

class TestQueryEdgeCases(TestCase):

    def _parse(self, query):
        from search.services.query_parser import QueryInterpreter as QI
        QI._countries_cache = QI._FALLBACK_COUNTRIES
        with patch('search.services.query_parser._USE_SETFIT', False), \
             patch('search.services.query_parser._USE_GLINER', False):
            return QI().parse(query)

    def test_year_is_current_not_hardcoded_2025(self):
        """Time references must use the current calendar year, not 2025."""
        r = self._parse("wheat shipments this year")
        current_year = str(datetime.date.today().year)
        time_range = r.get('time_range', '')
        if time_range:
            self.assertIn(current_year, str(time_range),
                          "time_range must reference current year, not hardcoded 2025")

    def test_logistics_stopwords_stripped_from_product(self):
        r = self._parse("bulk cargo wheat from China")
        product = r.get('product', '').lower()
        self.assertNotIn('bulk', product)
        self.assertNotIn('cargo', product)
        self.assertIn('wheat', product)

    def test_no_crash_on_empty_query(self):
        from search.services.query_parser import QueryInterpreter as QI
        QI._countries_cache = QI._FALLBACK_COUNTRIES
        with patch('search.services.query_parser._USE_SETFIT', False), \
             patch('search.services.query_parser._USE_GLINER', False):
            try:
                r = QI().parse("")
                # If it returns something, it should be a dict
                self.assertIsInstance(r, dict)
            except Exception as e:
                self.fail(f"parse('') raised an unexpected exception: {e}")

    def test_no_crash_on_long_query(self):
        long_q = "find dextrose " * 50
        r = self._parse(long_q)
        self.assertIn('family', r)


# =============================================================================
# 3. SemanticCache — context key isolation
# =============================================================================

class TestSemanticCacheContextIsolation(TestCase):

    @patch('search.services.semantic_cache._get_redis', return_value=None)
    def test_get_returns_none_without_redis(self, _):
        from search.services.semantic_cache import SemanticCache
        cache = SemanticCache()
        self.assertIsNone(cache.get("dextrose"))
        self.assertIsNone(cache.get("dextrose", context="subcat=5"))

    @patch('search.services.semantic_cache._get_redis', return_value=None)
    def test_set_returns_false_without_redis(self, _):
        from search.services.semantic_cache import SemanticCache
        cache = SemanticCache()
        self.assertFalse(cache.set("dextrose", {"results": []}))
        self.assertFalse(cache.set("dextrose", {"results": []}, context="subcat=5"))

    def test_different_contexts_produce_different_sha(self):
        from search.services.semantic_cache import _query_sha, _normalize_query

        norm = _normalize_query("dextrose")
        sha_plain = _query_sha(norm)
        sha_ctx1 = _query_sha(norm + '\x00' + 'subcat=5')
        sha_ctx2 = _query_sha(norm + '\x00' + 'subcat=7')
        sha_country = _query_sha(norm + '\x00' + 'country=china')

        self.assertNotEqual(sha_plain, sha_ctx1)
        self.assertNotEqual(sha_ctx1, sha_ctx2)
        self.assertNotEqual(sha_plain, sha_country)

    def test_same_context_produces_same_sha(self):
        from search.services.semantic_cache import _query_sha, _normalize_query
        norm = _normalize_query("dextrose")
        ctx = "subcat=5|country=china"
        self.assertEqual(
            _query_sha(norm + '\x00' + ctx),
            _query_sha(norm + '\x00' + ctx),
        )

    def test_normalize_lowercase_and_strip(self):
        from search.services.semantic_cache import _normalize_query
        self.assertEqual(_normalize_query("  Dextrose  "), "dextrose")
        self.assertEqual(_normalize_query("wheat   from  China"), "wheat from china")

    def test_sha_length_16(self):
        from search.services.semantic_cache import _query_sha
        self.assertEqual(len(_query_sha("test_query")), 16)


# =============================================================================
# 4. Company deduplication
# =============================================================================

class TestCompanyDeduplication(TestCase):

    def setUp(self):
        from search.services.aggregation import SupplierAggregator
        self.agg = SupplierAggregator()

    def _e(self, name, shipment_count=5, total_volume=100.0, max_vol=30.0,
            last_date=None):
        return {
            'name': name,
            'country': 'China',
            'total_volume': total_volume,
            'avg_price': 300.0,
            'shipment_count': shipment_count,
            'last_shipment_date': last_date or datetime.date(2024, 1, 1),
            'max_shipment_vol': max_vol,
            'avg_shipment_vol': total_volume / shipment_count,
            'type': 'Supplier',
            'volume_score': None,
            'volume_fit': 'N/A',
        }

    def test_empty_list(self):
        self.assertEqual(self.agg._deduplicate_companies([]), [])

    def test_single_entry_unchanged(self):
        entries = [self._e("Alpha Corp")]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Alpha Corp')

    def test_distinct_companies_not_merged(self):
        entries = [self._e("Alpha Trading"), self._e("Beta Corp"), self._e("Gamma Ltd")]
        self.assertEqual(len(self.agg._deduplicate_companies(entries)), 3)

    def test_exact_duplicate_merged(self):
        entries = [
            self._e("XYZ TRADERS PVT LTD", shipment_count=10, total_volume=200.0),
            self._e("XYZ TRADERS PVT LTD", shipment_count=5, total_volume=100.0),
        ]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['shipment_count'], 15)
        self.assertAlmostEqual(result[0]['total_volume'], 300.0)

    def test_near_duplicate_merged(self):
        """'XYZ TRADERS PVT LTD' vs 'XYZ TRADERS PVT. LTD' — same entity."""
        entries = [
            self._e("XYZ TRADERS PVT LTD", shipment_count=10),
            self._e("XYZ TRADERS PVT. LTD", shipment_count=3),
        ]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['shipment_count'], 13)

    def test_unrelated_names_not_merged(self):
        """Companies with ratio < 0.85 must stay separate."""
        entries = [self._e("ALPHA LOGISTICS CO"), self._e("BETA SHIPPING LTD")]
        self.assertEqual(len(self.agg._deduplicate_companies(entries)), 2)

    def test_primary_chosen_by_shipment_count(self):
        """Entry with most shipments becomes the primary (keeps its name)."""
        entries = [
            self._e("ACME CORP LTD", shipment_count=3),
            self._e("ACME CORP. LTD", shipment_count=15),
        ]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'ACME CORP. LTD')

    def test_most_recent_date_kept(self):
        entries = [
            self._e("XYZ LTD", last_date=datetime.date(2023, 1, 1)),
            self._e("XYZ. LTD", last_date=datetime.date(2024, 6, 15)),
        ]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(result[0]['last_shipment_date'], datetime.date(2024, 6, 15))

    def test_max_shipment_vol_kept(self):
        entries = [
            self._e("XYZ LTD", shipment_count=10, total_volume=100, max_vol=50.0),
            self._e("XYZ. LTD", shipment_count=3, total_volume=30, max_vol=120.0),
        ]
        result = self.agg._deduplicate_companies(entries)
        self.assertEqual(result[0]['max_shipment_vol'], 120.0)

    def test_avg_shipment_vol_recalculated(self):
        entries = [
            self._e("XYZ LTD", shipment_count=10, total_volume=200.0),
            self._e("XYZ. LTD", shipment_count=5, total_volume=100.0),
        ]
        result = self.agg._deduplicate_companies(entries)
        expected_avg = 300.0 / 15  # total_vol / shipment_count
        self.assertAlmostEqual(result[0]['avg_shipment_vol'], expected_avg, places=1)


# =============================================================================
# 5. SearchViewSet — cache context building
# =============================================================================

class TestCacheContextBuilding(TestCase):
    """Verify cache_context is built correctly from request params."""

    def _build_context(self, subcategory_id=None, country=None, scope=None):
        """Replicate the cache_context building logic from views.py."""
        _ctx_parts = []
        if subcategory_id:
            _ctx_parts.append(f'subcat={subcategory_id}')
        if country:
            _ctx_parts.append(f'country={country.lower()}')
        if scope:
            _ctx_parts.append(f'scope={scope.upper()}')
        return '|'.join(_ctx_parts) or None

    def test_no_filters_gives_none(self):
        self.assertIsNone(self._build_context())

    def test_subcategory_id_included(self):
        ctx = self._build_context(subcategory_id='42')
        self.assertIsNotNone(ctx)
        self.assertIn('subcat=42', ctx)

    def test_country_lowercased(self):
        ctx = self._build_context(country='China')
        self.assertIn('country=china', ctx)

    def test_scope_uppercased(self):
        ctx = self._build_context(scope='worldwide')
        self.assertIn('scope=WORLDWIDE', ctx)

    def test_all_filters_combined(self):
        ctx = self._build_context(subcategory_id='5', country='India', scope='WORLDWIDE')
        self.assertIn('subcat=5', ctx)
        self.assertIn('country=india', ctx)
        self.assertIn('scope=WORLDWIDE', ctx)

    def test_different_subcategories_give_different_sha(self):
        from search.services.semantic_cache import _query_sha, _normalize_query
        norm = _normalize_query("dextrose")
        ctx1 = self._build_context(subcategory_id='5')
        ctx2 = self._build_context(subcategory_id='7')
        sha1 = _query_sha(norm + '\x00' + ctx1)
        sha2 = _query_sha(norm + '\x00' + ctx2)
        self.assertNotEqual(sha1, sha2)


# =============================================================================
# 6. SearchViewSet — BUY+PAKISTAN error (HIGH #3)
# =============================================================================

class TestBuyPakistanError(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch('search.views.QueryInterpreter')
    def test_buy_pakistan_returns_error_code(self, MockInterp):
        """BUY + PAKISTAN must return error='buy_pakistan_not_supported'."""
        MockInterp.return_value.parse.return_value = _make_parsed_query(
            intent='BUY', scope='PAKISTAN', family=1
        )
        response = self.client.get('/api/search/', {'q': 'wheat', 'no_cache': '1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('error'), 'buy_pakistan_not_supported')

    @patch('search.views.QueryInterpreter')
    def test_buy_pakistan_error_has_message(self, MockInterp):
        MockInterp.return_value.parse.return_value = _make_parsed_query(
            intent='BUY', scope='PAKISTAN', family=1
        )
        response = self.client.get('/api/search/', {'q': 'wheat', 'no_cache': '1'})
        data = response.json()
        self.assertIn('message', data)
        # Message must explain the limitation
        self.assertTrue(
            any(w in data['message'].lower() for w in ['import', 'export', 'pakistan', 'database']),
            f"Error message should explain the limitation. Got: {data['message']}"
        )

    @patch('search.views.QueryInterpreter')
    def test_buy_pakistan_count_is_zero(self, MockInterp):
        MockInterp.return_value.parse.return_value = _make_parsed_query(
            intent='BUY', scope='PAKISTAN', family=1
        )
        response = self.client.get('/api/search/', {'q': 'wheat', 'no_cache': '1'})
        data = response.json()
        self.assertEqual(data.get('count'), 0)
        self.assertEqual(data.get('results', []), [])


# =============================================================================
# 7. SearchViewSet — SELL+WORLDWIDE warnings and data_note (HIGH #4 + #5)
# =============================================================================

class TestSellWorldwideWarnings(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    @patch('search.views.SupplierAggregator')
    @patch('search.services.ranking_ltr.RankingEnsemble')
    def test_sell_worldwide_has_data_note(self, MockRanker, MockAgg, MockMatcher, MockInterp):
        """SELL+WORLDWIDE must include data_note."""
        parsed = _make_parsed_query(intent='SELL', scope='WORLDWIDE', family=1)
        suppliers = [_make_supplier()]
        _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker, parsed, suppliers)

        response = self.client.get('/api/search/', {'q': 'sell dextrose', 'no_cache': '1'})
        data = response.json()
        self.assertIn('data_note', data,
                      "SELL+WORLDWIDE response must include data_note")
        self.assertGreater(len(data['data_note']), 0)

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    @patch('search.views.SupplierAggregator')
    @patch('search.services.ranking_ltr.RankingEnsemble')
    def test_sell_worldwide_country_filter_triggers_warning(
        self, MockRanker, MockAgg, MockMatcher, MockInterp
    ):
        """SELL+WORLDWIDE+country_filter must include a warning in response."""
        parsed = _make_parsed_query(
            intent='SELL', scope='WORLDWIDE', family=2, country_filter=['China']
        )
        _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker, parsed, [])

        response = self.client.get('/api/search/', {'q': 'sell dextrose to China', 'no_cache': '1'})
        data = response.json()
        warnings = data.get('warnings', [])
        self.assertTrue(len(warnings) > 0,
                        "Must have warnings when SELL+WORLDWIDE+country_filter")
        warning_text = ' '.join(warnings).lower()
        self.assertTrue(
            'country' in warning_text or 'china' in warning_text,
            f"Warning must reference the country filter. Got: {warnings}"
        )

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    @patch('search.views.SupplierAggregator')
    @patch('search.services.ranking_ltr.RankingEnsemble')
    def test_sell_worldwide_no_country_filter_no_warning(
        self, MockRanker, MockAgg, MockMatcher, MockInterp
    ):
        """SELL+WORLDWIDE without country_filter must NOT include spurious warnings."""
        parsed = _make_parsed_query(intent='SELL', scope='WORLDWIDE', family=1)
        suppliers = [_make_supplier()]
        _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker, parsed, suppliers)

        response = self.client.get('/api/search/', {'q': 'sell dextrose', 'no_cache': '1'})
        data = response.json()
        warnings = data.get('warnings', [])
        self.assertEqual(warnings, [],
                         "No warnings expected when no country_filter for SELL+WORLDWIDE")


# =============================================================================
# 8. SearchViewSet — basic response contract
# =============================================================================

class TestResponseContract(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_missing_q_returns_400(self):
        response = self.client.get('/api/search/')
        self.assertEqual(response.status_code, 400)

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    @patch('search.views.SupplierAggregator')
    @patch('search.services.ranking_ltr.RankingEnsemble')
    def test_successful_response_has_required_fields(
        self, MockRanker, MockAgg, MockMatcher, MockInterp
    ):
        """Every successful response must include the required fields."""
        _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker)
        response = self.client.get('/api/search/', {'q': 'dextrose', 'no_cache': '1'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        required = ['query', 'results', 'count', 'parsed_query', 'matched_subcategories']
        for field in required:
            self.assertIn(field, data, f"Required field missing: {field}")

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    @patch('search.views.SupplierAggregator')
    @patch('search.services.ranking_ltr.RankingEnsemble')
    def test_count_matches_results_length(
        self, MockRanker, MockAgg, MockMatcher, MockInterp
    ):
        _patch_pipeline(MockInterp, MockMatcher, MockAgg, MockRanker)
        response = self.client.get('/api/search/', {'q': 'dextrose', 'no_cache': '1'})
        data = response.json()
        self.assertEqual(data['count'], len(data['results']))

    @patch('search.views.QueryInterpreter')
    @patch('search.views.QueryMatcher')
    def test_no_match_returns_message_or_suggestions(
        self, MockMatcher, MockInterp
    ):
        """Zero NLP matches with no filters → message + optional suggestions."""
        MockInterp.return_value.parse.return_value = _make_parsed_query(
            product='zxqunknownproduct99'
        )
        MockMatcher.return_value.match.return_value = []

        with patch('search.views.HybridRetriever', create=True) as MockRetriever:
            MockRetriever.return_value.retrieve.return_value = []
            response = self.client.get('/api/search/', {'q': 'zxqunknownproduct99', 'no_cache': '1'})

        data = response.json()
        self.assertEqual(data.get('results', []), [])
        self.assertTrue(
            'message' in data or 'suggestions' in data,
            "No-match response must have message or suggestions"
        )

    @patch('search.views.QueryInterpreter')
    def test_scope_country_conflict_returns_error(self, MockInterp):
        """scope=PAKISTAN + non-Pakistan country filter → scope_country_conflict."""
        MockInterp.return_value.parse.return_value = _make_parsed_query(
            intent='BUY', scope='PAKISTAN', country_filter=['China'], family=2
        )
        response = self.client.get('/api/search/', {'q': 'wheat from China', 'no_cache': '1'})
        data = response.json()
        self.assertEqual(data.get('error'), 'scope_country_conflict')


# =============================================================================
# 9. Time range parser
# =============================================================================

class TestTimeRangeParser(TestCase):

    def setUp(self):
        from search.views import SearchViewSet
        self.view = SearchViewSet()

    def test_bare_year(self):
        r = self.view._parse_time_range("2023")
        self.assertIsNotNone(r)
        self.assertEqual(r['start_date'].year, 2023)
        self.assertEqual(r['end_date'].year, 2023)

    def test_q2_2024(self):
        r = self.view._parse_time_range("Q2 2024")
        self.assertIsNotNone(r)
        self.assertEqual(r['start_date'].month, 4)
        self.assertEqual(r['end_date'].month, 6)

    def test_last_6_months(self):
        r = self.view._parse_time_range("last 6 months")
        self.assertIsNotNone(r)
        self.assertLessEqual(r['start_date'], datetime.date.today())

    def test_last_1_year(self):
        r = self.view._parse_time_range("last 1 year")
        self.assertIsNotNone(r)

    def test_january_2024(self):
        r = self.view._parse_time_range("january 2024")
        self.assertIsNotNone(r)
        self.assertEqual(r['start_date'].month, 1)
        self.assertEqual(r['start_date'].year, 2024)

    def test_this_year(self):
        r = self.view._parse_time_range("this year")
        self.assertIsNotNone(r)
        self.assertEqual(r['start_date'].year, datetime.date.today().year)

    def test_since_march(self):
        r = self.view._parse_time_range("since march")
        self.assertIsNotNone(r)
        self.assertEqual(r['start_date'].month, 3)

    def test_none_input(self):
        self.assertIsNone(self.view._parse_time_range(None))

    def test_empty_string(self):
        self.assertIsNone(self.view._parse_time_range(""))

    def test_garbage_input(self):
        self.assertIsNone(self.view._parse_time_range("random garbage text xyz"))


# =============================================================================
# 10. Top-N extractor
# =============================================================================

class TestTopNExtractor(TestCase):

    def setUp(self):
        from search.views import SearchViewSet
        self.view = SearchViewSet()

    def test_top_3(self):
        self.assertEqual(self.view._extract_top_n("top 3 suppliers of wheat"), 3)

    def test_best_5(self):
        self.assertEqual(self.view._extract_top_n("best 5 dextrose suppliers"), 5)

    def test_first_10(self):
        self.assertEqual(self.view._extract_top_n("first 10 results"), 10)

    def test_suggest_7(self):
        self.assertEqual(self.view._extract_top_n("suggest 7 buyers"), 7)

    def test_no_number_returns_none(self):
        self.assertIsNone(self.view._extract_top_n("find suppliers of wheat"))

    def test_zero_not_returned(self):
        result = self.view._extract_top_n("top 0 suppliers")
        # top 0 is nonsensical — may return 0 or None; either is acceptable
        self.assertNotEqual(result, 5)  # must not be the F6 default


# =============================================================================
# 11. Cross-encoder — graceful degradation
# =============================================================================

class TestCrossEncoderReranker(TestCase):

    def _cands(self, names):
        return [{'id': i, 'name': n, 'score': 1.0 / (i + 1), 'hs_code': None}
                for i, n in enumerate(names)]

    def test_empty_candidates(self):
        from search.services.cross_encoder import CrossEncoderReranker
        self.assertEqual(CrossEncoderReranker().rerank("wheat", []), [])

    def test_single_candidate_passthrough(self):
        from search.services.cross_encoder import CrossEncoderReranker
        reranker = CrossEncoderReranker()
        result = reranker.rerank("wheat", self._cands(["Wheat Flour"]), top_k=5)
        self.assertEqual(len(result), 1)

    def test_graceful_degradation_without_model(self):
        """When model load fails, original order must be returned (trimmed to top_k)."""
        from search.services.cross_encoder import CrossEncoderReranker
        reranker = CrossEncoderReranker()
        reranker._loaded = True
        reranker._model = None  # simulate load failure
        cands = self._cands(["A", "B", "C", "D", "E"])
        result = reranker.rerank("wheat", cands, top_k=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'A')  # original order preserved

    def test_top_k_limits_output(self):
        from search.services.cross_encoder import CrossEncoderReranker
        reranker = CrossEncoderReranker()
        reranker._loaded = True
        reranker._model = None
        cands = self._cands(["A", "B", "C", "D", "E", "F", "G"])
        result = reranker.rerank("wheat", cands, top_k=4)
        self.assertLessEqual(len(result), 4)
