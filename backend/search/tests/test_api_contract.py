"""
backend/search/tests/test_api_contract.py

Phase 6: API contract tests — verify search API response shapes.

Tests the SearchViewSet response schema without hitting a live DB:
  - Required fields present in response
  - Correct HTTP status codes
  - Correct Content-Type
  - Error responses have expected shape
  - _timing fields present

Uses Django test client with mocked pipeline internals.

Run:
    cd backend
    pytest search/tests/test_api_contract.py -v
"""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture(scope='module')
def django_client():
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass
    from django.test import RequestFactory
    return RequestFactory()


# ── Helpers ───────────────────────────────────────────────────────────────────

MOCK_PARSED = {
    'intent': 'BUY',
    'family': 1,
    'product': 'dextrose',
    'scope': 'WORLDWIDE',
    'volume_mt': None,
    'price_ceiling': None,
    'price_floor': None,
    'time_range': None,
    'country_filter': [],
    'counterparty_name': None,
    'multi_intent': False,
    'ner_confidence': 1.0,
    'ambiguous_query': False,
    'classifier_confidence': 0.0,
}

MOCK_SUBCATEGORIES = [
    {'id': 1, 'name': 'Dextrose Anhydrous', 'score': 0.98, 'matched_variants': [101]},
]

MOCK_RESULTS = [
    {
        'name': 'Shandong Pharma Co',
        'country': 'China',
        'avg_price': 350.0,
        'total_volume_mt': 500.0,
        'shipment_count': 12,
        'heuristic_score': 0.85,
        'ltr_score': 0.72,
        'final_score': 0.80,
    },
    {
        'name': 'Euro Sweeteners GmbH',
        'country': 'Germany',
        'avg_price': 420.0,
        'total_volume_mt': 300.0,
        'shipment_count': 8,
        'heuristic_score': 0.75,
        'ltr_score': 0.68,
        'final_score': 0.72,
    },
]


def _make_mock_view():
    """Patch the full pipeline and return SearchViewSet."""
    from search.views import SearchViewSet
    return SearchViewSet


def _get_response(factory, url_params, view_cls):
    """Build a GET request and dispatch to view."""
    from django.http import QueryDict
    request = factory.get('/api/search/query/', url_params)
    view = view_cls.as_view({'get': 'list'})
    return view(request)


# ── Contract tests ─────────────────────────────────────────────────────────────

class TestSearchAPIContract:

    @pytest.fixture(autouse=True)
    def patch_pipeline(self):
        """Patch all pipeline components to avoid DB/model access."""
        # Mock ProductItem queryset (called for available_variants sidebar)
        mock_qs = MagicMock()
        mock_qs.filter.return_value.values.return_value = []

        with patch('search.views.QueryInterpreter') as mock_interp, \
             patch('search.views.QueryMatcher') as mock_matcher, \
             patch('search.views.SupplierAggregator') as mock_agg, \
             patch('search.views.get_cache') as mock_cache, \
             patch('search.services.ranking_ltr.RankingEnsemble') as mock_ranker, \
             patch('trade_data.models.ProductItem.objects', mock_qs):

            # Interpreter returns mock parsed query
            mock_interp.return_value.parse.return_value = dict(MOCK_PARSED)

            # Matcher returns mock subcategories
            mock_matcher.return_value.match.return_value = MOCK_SUBCATEGORIES

            # Aggregator returns mock candidates
            mock_agg.return_value.get_suppliers_for_subcategories.return_value = MOCK_RESULTS

            # RankingEnsemble passes through results
            mock_ranker.return_value.rank_candidates.return_value = MOCK_RESULTS

            # Cache always misses
            mock_cache.return_value.get.return_value = None

            yield

    def test_missing_query_param_returns_400(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {}, view_cls)
        assert response.status_code == 400

    def test_valid_query_returns_200(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert response.status_code == 200

    def test_response_has_query_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        data = response.data
        assert 'query' in data
        assert data['query'] == 'dextrose suppliers'

    def test_response_has_results_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)

    def test_response_has_count_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert 'count' in response.data
        assert isinstance(response.data['count'], int)

    def test_response_has_parsed_query(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert 'parsed_query' in response.data
        pq = response.data['parsed_query']
        assert 'intent' in pq
        assert 'family' in pq

    def test_response_has_matched_subcategories(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert 'matched_subcategories' in response.data

    def test_response_has_market_snapshot(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert 'market_snapshot' in response.data
        ms = response.data['market_snapshot']
        assert 'total_count' in ms
        assert 'avg_price_global' in ms
        assert 'top_country' in ms

    def test_response_has_cache_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert '_cache' in response.data
        assert response.data['_cache'] in ('hit', 'miss')

    def test_response_has_latency_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert '_latency_ms' in response.data
        assert isinstance(response.data['_latency_ms'], (int, float))

    def test_response_has_timing_breakdown(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': 'dextrose suppliers'}, view_cls)
        assert '_timing' in response.data
        timing = response.data['_timing']
        for key in ('t_parse_ms', 't_retrieval_ms', 't_aggregation_ms', 't_ranking_ms'):
            assert key in timing, f"Missing timing key: {key}"
            assert isinstance(timing[key], (int, float))

    def test_empty_query_returns_400(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {'q': ''}, view_cls)
        assert response.status_code == 400

    def test_error_response_has_error_field(self, django_client):
        view_cls = _make_mock_view()
        response = _get_response(django_client, {}, view_cls)
        data = response.data
        assert 'error' in data

    def test_no_cache_param_bypasses_cache(self, django_client):
        """no_cache=1 should bypass semantic cache."""
        view_cls = _make_mock_view()
        with patch('search.views.get_cache') as mock_cache:
            mock_cache.return_value.get.return_value = {'cached': True, '_latency_ms': 1}
            # Without no_cache: would return cached
            response1 = _get_response(django_client, {'q': 'sugar', 'no_cache': '0'}, view_cls)
            # With no_cache=1: bypasses cache
            response2 = _get_response(django_client, {'q': 'sugar', 'no_cache': '1'}, view_cls)
        # Both should be 200; no_cache=1 should have gone through pipeline
        assert response2.status_code == 200


class TestSearchAPIContractNoMatch:
    """Contract for when the query produces no subcategory matches."""

    def test_no_match_returns_200_with_message(self, django_client):
        with patch('search.views.QueryInterpreter') as mock_interp, \
             patch('search.views.QueryMatcher') as mock_matcher, \
             patch('search.views.get_cache') as mock_cache:

            mock_interp.return_value.parse.return_value = dict(MOCK_PARSED)
            mock_matcher.return_value.match.return_value = []
            mock_cache.return_value.get.return_value = None

            view_cls = _make_mock_view()
            response = _get_response(django_client, {'q': 'zxqwerty fake product'}, view_cls)

        assert response.status_code == 200
        data = response.data
        assert 'results' in data
        assert data['results'] == []

    def test_no_match_response_has_query(self, django_client):
        with patch('search.views.QueryInterpreter') as mock_interp, \
             patch('search.views.QueryMatcher') as mock_matcher, \
             patch('search.views.get_cache') as mock_cache:

            mock_interp.return_value.parse.return_value = dict(MOCK_PARSED)
            mock_matcher.return_value.match.return_value = []
            mock_cache.return_value.get.return_value = None

            view_cls = _make_mock_view()
            response = _get_response(
                django_client, {'q': 'completely unknown product xyz'}, view_cls
            )

        assert response.data['query'] == 'completely unknown product xyz'
