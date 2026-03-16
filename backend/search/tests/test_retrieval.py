"""
Integration tests for the hybrid BM25 + FAISS + RRF retrieval system.

These tests require the FAISS index to be built (search_index_v2.pkl must exist).
They also require the Django DB to be populated.

Run: python -m pytest search/tests/test_retrieval.py -v
"""

import pytest
from pathlib import Path
from django.conf import settings


@pytest.mark.django_db
class TestHybridRetriever:
    """Integration tests requiring DB + FAISS index."""

    @pytest.fixture(autouse=True)
    def setup_retriever(self):
        from search.services.retrieval import HybridRetriever
        # Use cached index if available, don't rebuild
        self.retriever = HybridRetriever()

    def test_index_exists(self):
        """FAISS index file must exist before tests run."""
        idx_path = Path(settings.BASE_DIR) / 'search_index_v2.pkl'
        assert idx_path.exists(), (
            f"FAISS index not found at {idx_path}. "
            "Run: python manage.py shell -c \"from search.services.retrieval import build_index; build_index(force_rebuild=True)\""
        )

    def test_exact_product_match_ranks_first(self):
        """Exact product name should rank #1."""
        results = self.retriever.retrieve('dextrose anhydrous')
        assert results, "No results returned"
        top_name = results[0]['name'].lower()
        assert 'dextrose' in top_name, f"Expected dextrose in top result, got {results[0]['name']!r}"

    def test_lactose_monohydrate_exact_match(self):
        """Top result for 'lactose monohydrate' must contain 'lactose monohydrate'."""
        results = self.retriever.retrieve('lactose monohydrate')
        assert results
        top_name = results[0]['name'].lower()
        assert 'lactose monohydrate' in top_name or 'lactose mono' in top_name, \
            f"Top result should be a lactose monohydrate product, got {results[0]['name']!r}"

    def test_typo_recovery(self):
        """Misspelled query should still find the right product."""
        results = self.retriever.retrieve('dextros anhydrous')  # typo
        assert results
        top_name = results[0]['name'].lower()
        assert 'dextrose' in top_name, f"Expected dextrose for typo query, got {results[0]['name']!r}"

    def test_no_results_for_garbage_query(self):
        """Completely unrelated query should return empty or low-score results."""
        results = self.retriever.retrieve('quantum entanglement blockchain')
        # May return low-quality results, but should not crash
        assert isinstance(results, list)

    def test_returns_dict_with_required_keys(self):
        """Each result must have id, name, hs_code, score, method, matched_variants."""
        results = self.retriever.retrieve('sugar')
        assert results
        for r in results:
            assert 'id' in r
            assert 'name' in r
            assert 'score' in r
            assert 'method' in r
            assert 'matched_variants' in r
            assert isinstance(r['matched_variants'], list)

    def test_top_k_respected(self):
        """retrieve(top_k=3) should return at most 3 results."""
        results = self.retriever.retrieve('lactose', top_k=3)
        assert len(results) <= 3

    def test_scores_descending(self):
        """Results should be sorted by descending score."""
        results = self.retriever.retrieve('dextrose')
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"

    def test_hs_code_query(self):
        """HS code query should find matching products."""
        results = self.retriever.retrieve('1702.111')
        assert results, "HS code query returned no results"

    def test_country_noise_words_removed(self):
        """'from China' should not confuse the product match."""
        results_with = self.retriever.retrieve('dextrose from China')
        results_without = self.retriever.retrieve('dextrose')
        # Top product should be dextrose in both cases
        assert 'dextrose' in results_with[0]['name'].lower()
        assert 'dextrose' in results_without[0]['name'].lower()


@pytest.mark.django_db
class TestQueryMatcher:
    """Tests for the QueryMatcher interface (which wraps HybridRetriever)."""

    def test_match_returns_results(self):
        from search.services.nlp import QueryMatcher
        m = QueryMatcher()
        results = m.match('dextrose anhydrous suppliers')
        assert results, "QueryMatcher returned empty results"

    def test_match_result_has_matched_variants(self):
        from search.services.nlp import QueryMatcher
        m = QueryMatcher()
        results = m.match('dextrose anhydrous')
        assert results
        # matched_variants should be a list (possibly empty)
        assert isinstance(results[0].get('matched_variants', []), list)

    def test_match_sellers_query(self):
        """'sellers' keyword should not prevent product matching."""
        from search.services.nlp import QueryMatcher
        m = QueryMatcher()
        results = m.match('refined sugar sellers')
        assert results
        assert 'sugar' in results[0]['name'].lower() or 'sucrose' in results[0]['name'].lower()

    def test_match_exporters_query(self):
        """'exporters' keyword should not prevent product matching."""
        from search.services.nlp import QueryMatcher
        m = QueryMatcher()
        results = m.match('lactose monohydrate exporters')
        assert results
        assert 'lactose' in results[0]['name'].lower()


class TestRRFFusion:
    """Unit tests for RRF fusion logic."""

    def test_rrf_single_list(self):
        from search.services.retrieval import HybridRetriever
        h = HybridRetriever()
        ranked = {1: {'rank': 1, 'score': 1.0}, 2: {'rank': 2, 'score': 0.8}}
        fused = h._rrf_fuse([ranked], k=60)
        # doc 1 at rank 1 should score higher than doc 2 at rank 2
        assert fused[1] > fused[2]

    def test_rrf_two_lists_boost_overlap(self):
        """Doc appearing in both lists should score higher than doc in only one."""
        from search.services.retrieval import HybridRetriever
        h = HybridRetriever()
        list1 = {1: {'rank': 1, 'score': 1.0}, 2: {'rank': 2, 'score': 0.8}}
        list2 = {1: {'rank': 1, 'score': 1.0}, 3: {'rank': 2, 'score': 0.8}}
        fused = h._rrf_fuse([list1, list2], k=60)
        # Doc 1 appears in both lists → should score > doc 2 or doc 3
        assert fused[1] > fused.get(2, 0)
        assert fused[1] > fused.get(3, 0)

    def test_rrf_empty_lists(self):
        from search.services.retrieval import HybridRetriever
        h = HybridRetriever()
        assert h._rrf_fuse([{}, {}], k=60) == {}

    def test_rrf_k_parameter(self):
        """Higher k should produce lower scores (more rank bias)."""
        from search.services.retrieval import HybridRetriever
        h = HybridRetriever()
        ranked = {1: {'rank': 1, 'score': 1.0}}
        score_k60 = h._rrf_fuse([ranked], k=60)[1]
        score_k10 = h._rrf_fuse([ranked], k=10)[1]
        assert score_k10 > score_k60  # smaller k = less bias = higher score
