"""
Tests for SupplierReranker (Phase 3-E cross-encoder on company profiles).

Unit tests mock the CrossEncoder model.
Integration tests use the real model (marked @pytest.mark.slow).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_supplier(name, country, volume=1000, shipments=10, price=400, ranking_score=0.8):
    return {
        'name': name,
        'country': country,
        'total_volume': volume,
        'shipment_count': shipments,
        'avg_price': price,
        'last_shipment_date': '2024-01-15',
        'ranking_score': ranking_score,
    }


def _make_reranker_with_mock(logits):
    from search.services.reranker import SupplierReranker
    r = SupplierReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array(logits, dtype=float)
    r._model = mock_model
    r._loaded = True
    return r


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestBuildProfile:

    def test_profile_non_empty(self):
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        c = _make_supplier('Test Co', 'China')
        profile = r._build_profile(c)
        assert len(profile) > 0
        assert 'Test Co' in profile

    def test_profile_handles_none_values(self):
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        c = {'name': None, 'country': None, 'total_volume': None,
             'shipment_count': None, 'avg_price': None, 'last_shipment_date': None}
        profile = r._build_profile(c)
        assert isinstance(profile, str)
        assert len(profile) > 0

    def test_profile_includes_country(self):
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        c = _make_supplier('Test Co', 'Germany', volume=5000)
        profile = r._build_profile(c)
        assert 'Germany' in profile
        assert '5000' in profile


class TestReranker:

    def test_rerank_changes_order(self):
        """CE score should change order when it strongly disagrees with heuristic."""
        # Use 3 candidates: heuristic says A > B > C, but CE strongly favors B.
        # With close heuristic scores, CE weight (0.3) is enough to push B above A.
        candidates = [
            _make_supplier('Wrong Company', 'India', ranking_score=0.81),
            _make_supplier('Dextrose Specialist', 'China', ranking_score=0.80),
            _make_supplier('Unrelated Co', 'USA', ranking_score=0.70),
        ]
        # CE logits: Wrong=0.0, Dextrose=10.0, Unrelated=2.0
        # After norm: heuristic=[1.0, 0.909, 0.0], ce=[0.0, 1.0, 0.286]
        # Blended: Wrong=0.7*1.0+0.3*0.0=0.70, Dextrose=0.7*0.909+0.3*1.0=0.936
        reranker = _make_reranker_with_mock([0.0, 10.0, 2.0])
        result = reranker.rerank('dextrose anhydrous', candidates, top_k=3)
        assert result[0]['name'] == 'Dextrose Specialist'

    def test_rerank_respects_top_k(self):
        candidates = [_make_supplier(f'Co{i}', 'China', ranking_score=0.9 - i*0.1)
                      for i in range(5)]
        reranker = _make_reranker_with_mock([5.0, 4.0, 3.0, 2.0, 1.0])
        result = reranker.rerank('sugar', candidates, top_k=3)
        assert len(result) == 3

    def test_cross_encoder_score_field_present(self):
        candidates = [_make_supplier('A', 'China'), _make_supplier('B', 'India')]
        reranker = _make_reranker_with_mock([3.0, 1.0])
        result = reranker.rerank('query', candidates, top_k=2)
        assert 'cross_encoder_score' in result[0]
        assert 'cross_encoder_score' in result[1]

    def test_skip_family_7(self):
        """Family 7 (country comparison) should bypass CE."""
        candidates = [_make_supplier('Co', 'China')]
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        mock_model = MagicMock()
        r._model = mock_model
        r._loaded = True
        result = r.rerank('dextrose by country', candidates, parsed_query={'family': 7}, top_k=1)
        mock_model.predict.assert_not_called()
        assert result[0]['cross_encoder_score'] == 0.0

    def test_skip_family_8(self):
        """Family 8 (evidence) should bypass CE."""
        candidates = [_make_supplier('Co', 'China')]
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        mock_model = MagicMock()
        r._model = mock_model
        r._loaded = True
        result = r.rerank('has Nestle bought dextrose', candidates, parsed_query={'family': 8}, top_k=1)
        mock_model.predict.assert_not_called()

    def test_empty_candidates_returns_empty(self):
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        result = r.rerank('query', [], top_k=5)
        assert result == []

    def test_graceful_degradation_on_model_failure(self):
        """If model.predict raises, returns candidates in original order."""
        candidates = [_make_supplier(f'Co{i}', 'China', ranking_score=0.9 - i*0.1)
                      for i in range(3)]
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError('OOM')
        r._model = mock_model
        r._loaded = True
        result = r.rerank('query', candidates, top_k=3)
        assert len(result) == 3
        assert result[0]['name'] == 'Co0'

    def test_caps_at_max_candidates(self):
        """Cross-encoder processes at most MAX_CANDIDATES; remainder gets score=0."""
        from search.services.reranker import MAX_CANDIDATES
        # Create more candidates than MAX_CANDIDATES
        n = MAX_CANDIDATES + 5
        candidates = [_make_supplier(f'Co{i}', 'China') for i in range(n)]
        logits = [float(i) for i in range(MAX_CANDIDATES)]
        reranker = _make_reranker_with_mock(logits)
        result = reranker.rerank('query', candidates, top_k=n)
        # Check that last 5 have ce_score=0.0
        remainder_scores = [c['cross_encoder_score'] for c in result
                            if c['cross_encoder_score'] == 0.0]
        assert len(remainder_scores) >= 5

    def test_singleton(self):
        import search.services.reranker as m
        m._reranker_instance = None
        from search.services.reranker import get_supplier_reranker
        r1 = get_supplier_reranker()
        r2 = get_supplier_reranker()
        assert r1 is r2
        m._reranker_instance = None


# ---------------------------------------------------------------------------
# Integration tests (real model)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestSupplierRerankerIntegration:

    @pytest.fixture(autouse=True)
    def check_model(self):
        try:
            from sentence_transformers import CrossEncoder
            CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2', device='cpu', max_length=256)
        except Exception:
            pytest.skip("cross-encoder model not available")

    def test_relevant_supplier_ranks_higher(self):
        """A dextrose specialist should rank above an unrelated company."""
        candidates = [
            _make_supplier('Dextrose Anhydrous Co', 'China', volume=5000, ranking_score=0.7),
            _make_supplier('Shoe Manufacturing Inc', 'Vietnam', volume=8000, ranking_score=0.9),
        ]
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        result = r.rerank('dextrose anhydrous suppliers', candidates, top_k=2)
        assert result[0]['name'] == 'Dextrose Anhydrous Co'

    def test_scores_are_numeric(self):
        from search.services.reranker import SupplierReranker
        r = SupplierReranker()
        candidates = [_make_supplier('Co A', 'China'), _make_supplier('Co B', 'India')]
        result = r.rerank('sugar suppliers', candidates, top_k=2)
        for c in result:
            assert isinstance(c.get('cross_encoder_score'), float)
            assert isinstance(c.get('ranking_score'), float)
