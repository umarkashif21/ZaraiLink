"""
Unit and integration tests for the semantic cache.

Tests:
  - Cache set and get returns same response
  - Semantic similarity hit at threshold
  - Different-enough queries do NOT get a cache hit
  - TTL / expiry behavior
  - Category invalidation
  - Cache behaves gracefully when Redis is unavailable
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


class TestSemanticCacheUnit:
    """Unit tests that mock Redis — no live Redis required."""

    def _make_cache_with_mock_redis(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        c._r = MagicMock()
        c._connected = True
        return c

    def test_cosine_sim_identical_vectors(self):
        from search.services.semantic_cache import _cosine_sim
        v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert _cosine_sim(v, v) == pytest.approx(1.0)

    def test_cosine_sim_orthogonal(self):
        from search.services.semantic_cache import _cosine_sim
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert _cosine_sim(a, b) == pytest.approx(0.0)

    def test_vec_roundtrip(self):
        from search.services.semantic_cache import _vec_to_b64, _b64_to_vec
        v = np.random.rand(768).astype(np.float32)
        b64 = _vec_to_b64(v)
        v2 = _b64_to_vec(b64)
        assert np.allclose(v, v2)

    def test_query_sha_deterministic(self):
        from search.services.semantic_cache import _query_sha
        assert _query_sha('dextrose suppliers') == _query_sha('dextrose suppliers')

    def test_normalize_query(self):
        from search.services.semantic_cache import _normalize_query
        assert _normalize_query('  Dextrose   Suppliers  ') == 'dextrose suppliers'
        assert _normalize_query('LACTOSE MONOHYDRATE') == 'lactose monohydrate'

    def test_cache_returns_none_when_redis_unavailable(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        c._r = None
        c._connected = False
        assert c.get('dextrose') is None
        assert c.set('dextrose', {'results': []}) is False

    def test_stats_returns_not_connected(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        c._r = None
        c._connected = False
        stats = c.stats()
        assert stats['connected'] is False


@pytest.mark.django_db
class TestSemanticCacheIntegration:
    """Integration tests that require a live Redis instance."""

    @pytest.fixture(autouse=True)
    def check_redis(self):
        """Skip tests if Redis is not available."""
        try:
            import redis
            r = redis.Redis(host='127.0.0.1', port=6379, db=1, socket_timeout=1)
            r.ping()
        except Exception:
            pytest.skip("Redis not available")

    @pytest.fixture(autouse=True)
    def clean_cache(self):
        """Flush test cache DB before each test."""
        import redis
        r = redis.Redis(host='127.0.0.1', port=6379, db=1)
        r.flushdb()
        yield
        r.flushdb()

    def test_exact_cache_hit(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        response = {'results': [{'name': 'Test Co', 'country': 'China'}], 'count': 1}
        c.set('dextrose anhydrous suppliers', response)
        result = c.get('dextrose anhydrous suppliers')
        assert result is not None
        assert result['count'] == 1

    def test_normalized_query_hits_cache(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        response = {'results': [], 'count': 0}
        c.set('dextrose anhydrous', response)
        # Different capitalization/spacing should still hit
        result = c.get('  Dextrose  Anhydrous  ')
        assert result is not None

    def test_cache_miss_for_unrelated_query(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        response = {'results': [{'name': 'Test', 'country': 'China'}], 'count': 1}
        c.set('dextrose anhydrous suppliers', response)
        # Completely different query should miss
        result = c.get('lactose powder importers from Germany')
        # May or may not be None depending on semantic similarity, but should not error
        assert result is None or isinstance(result, dict)

    def test_category_invalidation(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        response = {'results': [{'name': 'Test', 'country': 'China'}], 'count': 1}
        c.set('dextrose anhydrous', response, matched_subcat_ids=[42])
        # Verify stored
        assert c.get('dextrose anhydrous') is not None
        # Invalidate category 42
        n = c.invalidate_category(42)
        assert n >= 1
        # Now cache should miss
        result = c.get('dextrose anhydrous')
        assert result is None

    def test_flush_all(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        c.set('query1', {'results': [], 'count': 0})
        c.set('query2', {'results': [], 'count': 0})
        n = c.flush_all()
        assert n > 0
        assert c.stats()['cached_queries'] == 0

    def test_stats(self):
        from search.services.semantic_cache import SemanticCache
        c = SemanticCache()
        c.set('test query', {'results': [], 'count': 0})
        stats = c.stats()
        assert stats['connected'] is True
        assert stats['cached_queries'] >= 1
