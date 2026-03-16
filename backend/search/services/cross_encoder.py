"""
backend/search/services/cross_encoder.py

Cross-encoder re-ranking layer for subcategory candidate selection.

Strategy:
  1. HybridRetriever (BM25 + FAISS + RRF) fetches top-N candidate subcategories.
  2. This module re-scores each (query, subcategory_name) pair using a cross-encoder.
  3. Final top-K are passed to SupplierAggregator.

Model: cross-encoder/ms-marco-MiniLM-L6-v2
  - 6-layer MiniLM fine-tuned on MS MARCO for passage relevance
  - ~22 MB, ~5ms for 15 pairs on CPU
  - Score range: unbounded logits; higher = more relevant

Feature flag: SEARCH_USE_CROSS_ENCODER in settings.py (default True)

Design notes:
  - Lazy-loaded singleton to avoid import-time overhead
  - Graceful degradation: returns original order if model unavailable
  - top_k_in/top_k_out: retrieve more, re-rank, keep fewer
    (e.g. 15 from hybrid → cross-encoder → return 5)
  - blend_alpha: interpolate CE score with original RRF score
    final_score = alpha * ce_norm + (1-alpha) * rrf_norm
    Default alpha=0.6 (CE dominates but doesn't fully override retrieval signal)
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------
CE_MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L6-v2'
BLEND_ALPHA = 0.6        # weight of CE score in final blend
TOP_K_RETRIEVE = 15      # how many hybrid candidates to feed to CE
TOP_K_RETURN = 5         # how many to return after re-ranking
MIN_CE_SCORE = -10.0     # clamp floor (logit scale)
MAX_CE_SCORE = 10.0      # clamp ceiling


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------
_reranker_instance: Optional['CrossEncoderReranker'] = None


def get_reranker() -> 'CrossEncoderReranker':
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance


# -----------------------------------------------------------------------
# CrossEncoderReranker
# -----------------------------------------------------------------------

class CrossEncoderReranker:
    """
    Re-ranks subcategory candidates using a cross-encoder model.

    Usage:
        reranker = CrossEncoderReranker()
        candidates = [{'id': 1, 'name': 'Dextrose Anhydrous', 'score': 0.9, ...}, ...]
        reranked = reranker.rerank(query, candidates, top_k=5)
    """

    def __init__(self):
        self._model = None
        self._loaded = False
        self._load_error: Optional[str] = None

    def _load(self) -> bool:
        """Lazy-load the cross-encoder model."""
        if self._loaded:
            return self._model is not None

        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(
                CE_MODEL_NAME,
                device='cpu',
                max_length=128,
            )
            self._loaded = True
            logger.info(f"CrossEncoder loaded: {CE_MODEL_NAME}")
            return True
        except Exception as e:
            self._load_error = str(e)
            self._loaded = True          # mark as attempted so we don't retry
            logger.warning(f"CrossEncoder load failed ({e}); will use retrieval-only order")
            return False

    # ------------------------------------------------------------------

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = TOP_K_RETURN,
        blend_alpha: float = BLEND_ALPHA,
    ) -> list[dict]:
        """
        Re-rank subcategory candidates for a query.

        Args:
            query:         original (or cleaned) query string
            candidates:    list of dicts with at least {'id', 'name', 'score'}
            top_k:         number of candidates to return
            blend_alpha:   weight of CE score vs original retrieval score

        Returns:
            Re-ranked list of up to top_k candidate dicts.
            Each dict gains a 'ce_score' field (raw logit) and
            the 'score' field is updated to the blended value.
        """
        if not candidates:
            return candidates

        # If only one candidate, nothing to re-rank
        if len(candidates) == 1:
            return candidates[:top_k]

        if not self._load():
            # Model unavailable — return original order, trimmed
            logger.debug("CrossEncoder unavailable, using retrieval order")
            return candidates[:top_k]

        try:
            return self._rerank_internal(query, candidates, top_k, blend_alpha)
        except Exception as e:
            logger.warning(f"CrossEncoder rerank failed ({e}), using retrieval order")
            return candidates[:top_k]

    def _rerank_internal(
        self,
        query: str,
        candidates: list[dict],
        top_k: int,
        blend_alpha: float,
    ) -> list[dict]:
        """Inner re-ranking with score blending."""
        # Build (query, passage) pairs
        # Use subcategory name as the passage; optionally include HS code
        pairs = []
        for c in candidates:
            passage = c['name']
            if c.get('hs_code'):
                passage = f"{passage} (HS {c['hs_code']})"
            pairs.append((query, passage))

        # Score all pairs in one forward pass
        ce_logits = self._model.predict(pairs, show_progress_bar=False)

        # Normalize CE logits to [0, 1]
        clipped = np.clip(ce_logits, MIN_CE_SCORE, MAX_CE_SCORE)
        ce_min, ce_max = clipped.min(), clipped.max()
        if ce_max > ce_min:
            ce_norm = (clipped - ce_min) / (ce_max - ce_min)
        else:
            ce_norm = np.ones(len(clipped)) * 0.5

        # Normalize original retrieval scores to [0, 1]
        orig_scores = np.array([c.get('score', 0.0) for c in candidates], dtype=float)
        s_min, s_max = orig_scores.min(), orig_scores.max()
        if s_max > s_min:
            orig_norm = (orig_scores - s_min) / (s_max - s_min)
        else:
            orig_norm = np.ones(len(orig_scores)) * 0.5

        # Blend
        blended = blend_alpha * ce_norm + (1.0 - blend_alpha) * orig_norm

        # Attach scores and sort
        for i, c in enumerate(candidates):
            c = dict(c)           # avoid mutating caller's dicts
            c['ce_score'] = round(float(ce_logits[i]), 4)
            c['score'] = round(float(blended[i]), 4)
            candidates[i] = c

        ranked = sorted(candidates, key=lambda x: x['score'], reverse=True)

        logger.debug(
            "CrossEncoder rerank: top=%s ce=%.3f blend=%.3f for query=%r",
            ranked[0]['name'] if ranked else '-',
            float(ce_logits[0]) if len(ce_logits) else 0,
            float(blended[0]) if len(blended) else 0,
            query,
        )

        return ranked[:top_k]
