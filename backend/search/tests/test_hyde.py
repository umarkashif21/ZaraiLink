"""
Tests for HyDE (Hypothetical Document Embeddings) — Phase 4-B.

Unit tests: no LLM or FAISS required.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


def _make_expander():
    from search.services.hyde import HyDEExpander
    e = HyDEExpander()
    e._openai_available = False  # force template fallback
    return e


class TestHyDEExpander:

    def test_template_profile_contains_query_terms(self):
        e = _make_expander()
        profile = e.generate_hypothetical_profile('sugar suppliers')
        assert 'sugar' in profile.lower()

    def test_template_profile_non_empty(self):
        e = _make_expander()
        profile = e.generate_hypothetical_profile('dextrose anhydrous')
        assert len(profile) > 20

    def test_cache_returns_same_text(self):
        e = _make_expander()
        p1 = e.generate_hypothetical_profile('lactose monohydrate')
        p2 = e.generate_hypothetical_profile('lactose monohydrate')
        assert p1 == p2

    def test_cache_different_queries_different_text(self):
        e = _make_expander()
        p1 = e.generate_hypothetical_profile('sugar')
        p2 = e.generate_hypothetical_profile('dextrose')
        assert p1 != p2

    def test_expand_skips_non_f1_family(self):
        """HyDE should NOT apply to F2-F9 queries."""
        e = _make_expander()
        dummy_vec = np.ones(768, dtype=np.float32)
        for family in [2, 3, 4, 5, 6, 7, 8, 9]:
            _, hyde_used = e.expand('sugar', family=family, query_vec=dummy_vec)
            assert hyde_used is False, f"HyDE should be skipped for family={family}"

    def test_expand_skips_long_queries(self):
        """Queries with more than 4 words should skip HyDE."""
        e = _make_expander()
        dummy_vec = np.ones(768, dtype=np.float32)
        long_query = 'dextrose anhydrous suppliers from China with high volume'
        _, hyde_used = e.expand(long_query, family=1, query_vec=dummy_vec)
        assert hyde_used is False

    def test_expand_applies_to_short_f1(self):
        """Short F1 queries should use HyDE."""
        e = _make_expander()
        dummy_q_vec = np.random.rand(768).astype(np.float32)
        dummy_q_vec /= np.linalg.norm(dummy_q_vec)

        # Mock encode_hypothetical to return a fake vector
        with patch.object(e, 'encode_hypothetical') as mock_enc:
            hyde_vec = np.random.rand(768).astype(np.float32)
            hyde_vec /= np.linalg.norm(hyde_vec)
            mock_enc.return_value = hyde_vec

            blended, hyde_used = e.expand('sugar', family=1, query_vec=dummy_q_vec)

        assert hyde_used is True
        assert blended is not None
        assert blended.shape == (768,)

    def test_blended_vector_is_normalized(self):
        """Blended embedding should have unit L2 norm."""
        e = _make_expander()
        dummy_q_vec = np.random.rand(768).astype(np.float32)
        dummy_q_vec /= np.linalg.norm(dummy_q_vec)

        with patch.object(e, 'encode_hypothetical') as mock_enc:
            hyde_vec = np.random.rand(768).astype(np.float32)
            hyde_vec /= np.linalg.norm(hyde_vec)
            mock_enc.return_value = hyde_vec

            blended, hyde_used = e.expand('sugar', family=1, query_vec=dummy_q_vec)

        if hyde_used:
            norm = np.linalg.norm(blended)
            assert abs(norm - 1.0) < 1e-5, f"Blended vector norm={norm:.6f}, expected ~1.0"

    def test_expand_returns_original_when_encoding_fails(self):
        """If encode_hypothetical fails, return original query_vec."""
        e = _make_expander()
        dummy_vec = np.random.rand(768).astype(np.float32)

        with patch.object(e, 'encode_hypothetical') as mock_enc:
            mock_enc.return_value = None   # encoding failure

            blended, hyde_used = e.expand('sugar', family=1, query_vec=dummy_vec)

        assert hyde_used is False
        assert np.allclose(blended, dummy_vec)

    def test_expand_no_crash_when_query_vec_is_none(self):
        e = _make_expander()
        result, hyde_used = e.expand('sugar', family=1, query_vec=None)
        assert result is None
        assert hyde_used is False

    def test_hyde_disabled_when_no_openai_key(self):
        """Template-based fallback should work without API key."""
        e = _make_expander()
        assert e._openai_available is False
        profile = e.generate_hypothetical_profile('palm oil')
        assert len(profile) > 0  # template still generates something

    def test_singleton_reuse(self):
        import search.services.hyde as m
        m._expander_instance = None
        from search.services.hyde import get_hyde_expander
        e1 = get_hyde_expander()
        e2 = get_hyde_expander()
        assert e1 is e2
        m._expander_instance = None
