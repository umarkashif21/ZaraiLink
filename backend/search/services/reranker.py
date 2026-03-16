"""
backend/search/services/reranker.py

Cross-encoder re-ranking of supplier candidates (Phase 3-E).

Re-ranks final company/supplier results after heuristic + LTR scoring,
using a cross-encoder to score (query, company_profile) relevance.

Model: cross-encoder/ms-marco-MiniLM-L6-v2
  - Trained on MS MARCO passage retrieval
  - ~22 MB, ~10ms for 50 candidates on CPU

Ensemble formula:
    final = 0.4 * norm_heuristic + 0.3 * norm_ltr + 0.3 * norm_ce

Skip conditions (family 7 and 8 bypass cross-encoder):
  - F7: country comparison — result is a market list, not a supplier ranking
  - F8: evidence retrieval — specific transaction lookup, not ranking

Lazy loading via module-level singleton.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------
CE_MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L6-v2'
MAX_CANDIDATES = 50          # cap for CE inference to bound latency
ENSEMBLE_W_HEURISTIC = 0.4
ENSEMBLE_W_LTR = 0.3
ENSEMBLE_W_CE = 0.3
# Families that skip cross-encoder re-ranking
SKIP_FAMILIES = {7, 8}


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------
_reranker_instance: Optional['SupplierReranker'] = None


def get_supplier_reranker() -> 'SupplierReranker':
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = SupplierReranker()
    return _reranker_instance


# -----------------------------------------------------------------------
# SupplierReranker
# -----------------------------------------------------------------------

class SupplierReranker:
    """
    Cross-encoder re-ranker for supplier/company search results.

    Takes the sorted list of supplier candidates (output of RankingEnsemble)
    and re-ranks them using a cross-encoder on (query, company_profile) pairs.

    Usage:
        reranker = SupplierReranker()
        ranked = reranker.rerank(query, candidates, parsed_query, top_k=10)
    """

    def __init__(self):
        self._model = None
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return self._model is not None
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(
                CE_MODEL_NAME,
                device='cpu',
                max_length=256,
            )
            self._loaded = True
            logger.info(f"SupplierReranker: CrossEncoder loaded ({CE_MODEL_NAME})")
            return True
        except Exception as e:
            self._loaded = True
            logger.warning(f"SupplierReranker: CrossEncoder load failed ({e})")
            return False

    # ------------------------------------------------------------------

    def _build_profile(self, candidate: dict) -> str:
        """
        Build a textual profile string for a supplier candidate.

        Handles None gracefully for all fields.
        """
        name = candidate.get('name') or candidate.get('company_name') or 'Unknown Company'
        country = candidate.get('country') or 'Unknown Country'
        volume = candidate.get('total_volume') or candidate.get('total_volume_mt') or 0
        shipments = candidate.get('shipment_count') or 0
        avg_price = candidate.get('avg_price') or candidate.get('avg_price_usd_mt')
        last_date = candidate.get('last_shipment_date') or 'N/A'

        price_str = f"${avg_price:.0f}/MT" if avg_price else "N/A"
        vol_str = f"{volume:.0f} MT" if volume else "N/A"

        return (
            f"Company: {name}. "
            f"Country: {country}. "
            f"Trade volume: {vol_str}. "
            f"Shipments: {shipments}. "
            f"Average price: {price_str}. "
            f"Last active: {last_date}."
        )

    # ------------------------------------------------------------------

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        parsed_query: Optional[dict] = None,
        top_k: int = 10,
    ) -> list[dict]:
        """
        Re-rank supplier candidates using cross-encoder.

        Args:
            query:         original query string
            candidates:    supplier dicts with 'ranking_score' (or 'score') field
            parsed_query:  parsed query dict (for skip conditions)
            top_k:         number of results to return

        Returns:
            Top-k re-ranked candidates with 'cross_encoder_score' field added
            and 'ranking_score' updated to blended value.
        """
        if not candidates:
            return candidates

        # Skip conditions
        family = (parsed_query or {}).get('family', 1)
        if family in SKIP_FAMILIES:
            logger.debug(f"SupplierReranker: skipping (family={family})")
            for c in candidates:
                c['cross_encoder_score'] = 0.0
            return candidates[:top_k]

        if not self._load():
            for c in candidates:
                c['cross_encoder_score'] = 0.0
            return candidates[:top_k]

        try:
            return self._rerank_internal(query, candidates, top_k)
        except Exception as e:
            logger.warning(f"SupplierReranker: inference failed ({e}), using heuristic order")
            for c in candidates:
                c['cross_encoder_score'] = 0.0
            return candidates[:top_k]

    def _rerank_internal(self, query: str, candidates: list, top_k: int) -> list:
        """Core re-ranking logic."""
        # Cap at MAX_CANDIDATES to bound latency
        pool = candidates[:MAX_CANDIDATES]

        # Build (query, profile) pairs
        pairs = [(query, self._build_profile(c)) for c in pool]

        # Forward pass
        ce_logits = self._model.predict(
            pairs,
            batch_size=16,
            show_progress_bar=False,
        )

        # Normalize all three score components to [0, 1]
        def _norm(arr):
            a_min, a_max = arr.min(), arr.max()
            if a_max > a_min:
                return (arr - a_min) / (a_max - a_min)
            return np.ones_like(arr) * 0.5

        ce_arr = np.array(ce_logits, dtype=float)
        heuristic_arr = np.array(
            [c.get('ranking_score') or c.get('score') or 0.0 for c in pool],
            dtype=float,
        )
        # LTR score may not be directly available; approximate from ranking_score
        # (the current ranking_score is already 70% heuristic + 30% LTR blend)
        # Use it directly as the heuristic component and set ltr_norm = 0
        # when not separately tracked.
        ltr_arr = np.array(
            [c.get('ltr_score') or 0.0 for c in pool],
            dtype=float,
        )

        ce_norm = _norm(ce_arr)
        heuristic_norm = _norm(heuristic_arr)
        ltr_norm = _norm(ltr_arr) if ltr_arr.any() else np.zeros(len(pool))

        # If no separate LTR, absorb its weight into heuristic
        if not ltr_arr.any():
            w_h = ENSEMBLE_W_HEURISTIC + ENSEMBLE_W_LTR
            w_ltr = 0.0
        else:
            w_h = ENSEMBLE_W_HEURISTIC
            w_ltr = ENSEMBLE_W_LTR

        blended = w_h * heuristic_norm + w_ltr * ltr_norm + ENSEMBLE_W_CE * ce_norm

        # Write scores back
        for i, c in enumerate(pool):
            c = dict(c)
            c['cross_encoder_score'] = round(float(ce_arr[i]), 4)
            c['ranking_score'] = round(float(blended[i]), 4)
            pool[i] = c

        # Candidates beyond MAX_CANDIDATES get cross_encoder_score=0
        remainder = []
        for c in candidates[MAX_CANDIDATES:]:
            c = dict(c)
            c['cross_encoder_score'] = 0.0
            remainder.append(c)

        ranked = sorted(pool, key=lambda x: x['ranking_score'], reverse=True)
        ranked.extend(remainder)

        logger.debug(
            "SupplierReranker: top=%s ce=%.3f blend=%.3f for query=%r",
            ranked[0].get('name') or ranked[0].get('company_name') if ranked else '-',
            float(ce_arr[0]) if len(ce_arr) else 0,
            float(blended[0]) if len(blended) else 0,
            query,
        )

        return ranked[:top_k]
