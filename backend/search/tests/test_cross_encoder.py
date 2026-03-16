"""
Tests for cross-encoder re-ranking module.

Unit tests mock the CrossEncoder model — no live download required.
Integration test loads the actual model (slow, ~5s first run).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candidates(names, scores=None):
    if scores is None:
        scores = [1.0 - 0.1 * i for i in range(len(names))]
    return [
        {'id': i + 1, 'name': name, 'score': scores[i], 'hs_code': None}
        for i, name in enumerate(names)
    ]


# ---------------------------------------------------------------------------
# Unit tests (mocked model)
# ---------------------------------------------------------------------------

class TestCrossEncoderUnit:

    def _make_reranker_with_mock(self, logits):
        """Create a CrossEncoderReranker whose model.predict() returns `logits`."""
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array(logits, dtype=float)
        r._model = mock_model
        r._loaded = True
        return r

    def test_rerank_orders_by_ce_score(self):
        """Candidate with highest CE score should rank first."""
        candidates = _make_candidates(
            ['Lactose Monohydrate', 'Dextrose Anhydrous', 'Sucrose'],
            scores=[0.9, 0.8, 0.7],
        )
        # CE logits: Dextrose scores highest
        reranker = self._make_reranker_with_mock([2.0, 8.0, 1.0])
        result = reranker.rerank('dextrose', candidates, top_k=3)
        assert result[0]['name'] == 'Dextrose Anhydrous'

    def test_rerank_respects_top_k(self):
        candidates = _make_candidates(
            ['A', 'B', 'C', 'D', 'E'],
            scores=[0.9, 0.8, 0.7, 0.6, 0.5],
        )
        reranker = self._make_reranker_with_mock([1.0, 2.0, 3.0, 4.0, 5.0])
        result = reranker.rerank('query', candidates, top_k=3)
        assert len(result) == 3

    def test_rerank_attaches_ce_score_field(self):
        candidates = _make_candidates(['Glucose', 'Fructose'])
        reranker = self._make_reranker_with_mock([3.5, 1.2])
        result = reranker.rerank('glucose', candidates, top_k=2)
        assert 'ce_score' in result[0]
        assert 'ce_score' in result[1]

    def test_rerank_blends_scores(self):
        """Blended score = alpha * ce_norm + (1-alpha) * orig_norm — must lie in [0, 1]."""
        candidates = _make_candidates(['X', 'Y', 'Z'], scores=[0.9, 0.5, 0.1])
        reranker = self._make_reranker_with_mock([5.0, 3.0, -1.0])
        result = reranker.rerank('x', candidates, top_k=3, blend_alpha=0.6)
        for r in result:
            assert 0.0 <= r['score'] <= 1.0, f"score out of range: {r['score']}"

    def test_single_candidate_passthrough(self):
        """Single candidate should be returned without CE inference."""
        candidates = _make_candidates(['Only One'])
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        r._loaded = True
        r._model = MagicMock()  # should not be called
        result = r.rerank('query', candidates, top_k=5)
        assert len(result) == 1
        r._model.predict.assert_not_called()

    def test_empty_candidates_returns_empty(self):
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        result = r.rerank('query', [], top_k=5)
        assert result == []

    def test_graceful_degradation_on_model_failure(self):
        """If model.predict raises, returns candidates in original order."""
        candidates = _make_candidates(['A', 'B', 'C'])
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("CUDA OOM")
        r._model = mock_model
        r._loaded = True
        result = r.rerank('query', candidates, top_k=3)
        # Should return original top_k in original order
        assert len(result) == 3
        assert result[0]['name'] == 'A'

    def test_model_load_failure_uses_retrieval_order(self):
        """If model cannot be loaded, returns original order trimmed to top_k."""
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        r._loaded = True
        r._model = None           # simulate failed load
        candidates = _make_candidates(['X', 'Y', 'Z', 'W'])
        result = r.rerank('query', candidates, top_k=2)
        assert len(result) == 2
        assert result[0]['name'] == 'X'   # original order preserved

    def test_hs_code_included_in_passage(self):
        """When hs_code is present, it should be included in the passage sent to CE."""
        candidates = [
            {'id': 1, 'name': 'Dextrose Anhydrous', 'score': 0.9, 'hs_code': '1702.11'},
            {'id': 2, 'name': 'Glucose Syrup', 'score': 0.7, 'hs_code': None},
        ]
        from search.services.cross_encoder import CrossEncoderReranker
        r = CrossEncoderReranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([5.0, 1.0])
        r._model = mock_model
        r._loaded = True
        r.rerank('dextrose 1702', candidates, top_k=2)
        # Check the passage passed to predict
        call_args = mock_model.predict.call_args
        pairs = call_args[0][0]
        # First candidate passage should contain the HS code
        assert '1702.11' in pairs[0][1]


# ---------------------------------------------------------------------------
# Integration test (loads real model — skip if model download fails)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestCrossEncoderIntegration:

    @pytest.fixture(autouse=True)
    def check_model(self):
        try:
            from sentence_transformers import CrossEncoder
            CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2', device='cpu', max_length=128)
        except Exception:
            pytest.skip("cross-encoder model not available")

    def test_dextrose_ranks_above_unrelated(self):
        from search.services.cross_encoder import CrossEncoderReranker
        candidates = _make_candidates([
            'Dextrose Anhydrous',
            'Lactose Monohydrate',
            'Sucrose',
            'Sodium Chloride',
        ], scores=[0.8, 0.75, 0.70, 0.65])
        r = CrossEncoderReranker()
        result = r.rerank('dextrose anhydrous suppliers from China', candidates, top_k=4)
        assert result[0]['name'] == 'Dextrose Anhydrous'

    def test_scores_are_in_0_1_range(self):
        from search.services.cross_encoder import CrossEncoderReranker
        candidates = _make_candidates(
            ['Whey Protein Concentrate', 'Milk Protein', 'Casein'],
            scores=[0.9, 0.8, 0.7],
        )
        r = CrossEncoderReranker()
        result = r.rerank('whey protein suppliers', candidates, top_k=3)
        for c in result:
            assert 0.0 <= c['score'] <= 1.0

    def test_singleton_reuse(self):
        """get_reranker() should return the same instance each time."""
        from search.services.cross_encoder import get_reranker
        # Reset singleton
        import search.services.cross_encoder as ce_module
        ce_module._reranker_instance = None
        r1 = get_reranker()
        r2 = get_reranker()
        assert r1 is r2
