"""
backend/search/services/nlp.py

QueryMatcher: matches a raw query string to ProductSubCategory IDs.

v2: Routes through HybridRetriever (BM25 + FAISS-HNSW + RRF + nomic-embed-text-v1)
    + optional cross-encoder re-ranking of top subcategory candidates.

Feature flags (settings.py):
    SEARCH_USE_HYBRID_RETRIEVAL (default True)
        True  → BM25 + FAISS + RRF (nomic-embed-text-v1)
        False → Legacy brute-force cosine (all-MiniLM-L6-v2)
    SEARCH_USE_CROSS_ENCODER (default True)
        True  → cross-encoder/ms-marco-MiniLM-L6-v2 re-ranks top-15 → top-5
        False → use retrieval order as-is
"""

import os
import pickle
import logging
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# Feature flags
USE_HYBRID = getattr(settings, 'SEARCH_USE_HYBRID_RETRIEVAL', True)
USE_CROSS_ENCODER = getattr(settings, 'SEARCH_USE_CROSS_ENCODER', True)


class QueryMatcher:
    """
    Matches natural language queries to ProductSubCategory IDs.

    Returns list of dicts: {id, name, hs_code, score, method, matched_variants}
    sorted by descending score.
    """

    # Legacy v1 singletons (kept for fallback)
    _model = None
    _index = None

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def match(self, query: str) -> list[dict]:
        """
        Main entry point.

        Returns up to 10 matching ProductSubCategory dicts with scores.

        If the full query phrase returns no results, falls back to trying
        each individual token — so partial words like "sug" still find
        "sugar" via the keyword icontains path.
        """
        results = self._match_core(query)
        if not results and len(query.split()) > 1:
            # Multi-word phrase failed — try longest individual token
            tokens = sorted(query.split(), key=len, reverse=True)
            for token in tokens:
                if len(token) >= 3:
                    results = self._match_core(token)
                    if results:
                        logger.info(f"Token fallback: {query!r} → {token!r} → {len(results)} results")
                        break
        return results

    def _match_core(self, query: str) -> list[dict]:
        """Internal: run hybrid or legacy match for a single query string."""
        if USE_HYBRID:
            try:
                return self._match_hybrid(query)
            except Exception as e:
                logger.warning(f"Hybrid retrieval failed ({e}), falling back to legacy")
                return self._match_legacy(query)
        else:
            return self._match_legacy(query)

    # -----------------------------------------------------------------------
    # Hybrid path (BM25 + FAISS + RRF)
    # -----------------------------------------------------------------------

    def _match_hybrid(self, query: str) -> list[dict]:
        """Route to HybridRetriever, optionally cross-encoder re-rank, enrich with variants."""
        from search.services.retrieval import HybridRetriever

        retriever = HybridRetriever()

        if USE_CROSS_ENCODER:
            # Fetch more candidates so CE has a wider pool to re-rank
            from search.services.cross_encoder import (
                get_reranker, TOP_K_RETRIEVE, TOP_K_RETURN,
            )
            raw_results = retriever.retrieve(query, top_k=TOP_K_RETRIEVE)
            reranker = get_reranker()
            results = reranker.rerank(query, raw_results, top_k=TOP_K_RETURN)
        else:
            results = retriever.retrieve(query, top_k=10)

        # Enrich each result with matched_variants (for sidebar + product-item filtering)
        clean_q = query.lower()
        for r in results:
            if not r.get('matched_variants'):
                r['matched_variants'] = self._find_variants(r['id'], clean_q)

        return results

    def _find_variants(self, subcat_id: int, clean_query: str) -> list[int]:
        """Find ProductItem IDs within a subcategory that match the query."""
        from trade_data.models import ProductItem
        from difflib import SequenceMatcher

        variants = []
        items = ProductItem.objects.filter(sub_category_id=subcat_id).values('id', 'name')

        for item in items:
            item_name_lower = item['name'].lower()
            # Exact substring match
            if clean_query in item_name_lower or item_name_lower in clean_query:
                variants.append(item['id'])
                continue
            # Fuzzy match for typos
            ratio = SequenceMatcher(None, clean_query, item_name_lower).ratio()
            if ratio > 0.85:
                variants.append(item['id'])

        return variants

    # -----------------------------------------------------------------------
    # Legacy path (all-MiniLM-L6-v2, brute-force cosine)
    # -----------------------------------------------------------------------

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device='cpu',
                model_kwargs={'low_cpu_mem_usage': False},
            )
        return cls._model

    @classmethod
    def get_index(cls):
        if cls._index is None:
            index_path = os.path.join(settings.BASE_DIR, 'search_index.pkl')
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    cls._index = pickle.load(f)
        return cls._index

    def _match_legacy(self, query: str) -> list[dict]:
        """Legacy brute-force cosine matching (all-MiniLM-L6-v2)."""
        from sklearn.metrics.pairwise import cosine_similarity
        from trade_data.models import ProductSubCategory, ProductItem
        from difflib import SequenceMatcher

        clean_qs = self._clean_query(query)
        matches = {}

        # Keyword match
        subcat_hits = ProductSubCategory.objects.filter(name__icontains=clean_qs)
        for hit in subcat_hits:
            matches[hit.id] = {
                'id': hit.id, 'name': hit.name, 'score': 1.0,
                'hs_code': hit.hs_code, 'method': 'keyword_subcat',
                'matched_variants': [],
            }

        item_hits = ProductItem.objects.filter(
            name__icontains=clean_qs
        ).select_related('sub_category')
        for item in item_hits:
            parent = item.sub_category
            if parent.id in matches:
                if item.id not in matches[parent.id]['matched_variants']:
                    matches[parent.id]['matched_variants'].append(item.id)
                    matches[parent.id]['variant_name'] = item.name
            else:
                matches[parent.id] = {
                    'id': parent.id, 'name': parent.name, 'score': 1.0,
                    'hs_code': parent.hs_code, 'method': 'keyword_item',
                    'matched_variants': [item.id], 'variant_name': item.name,
                }

        # Semantic search
        index = self.get_index()
        if index and index.get('embeddings') is not None:
            model = self.get_model()
            query_vec = model.encode([clean_qs])
            scores = cosine_similarity(query_vec, index['embeddings'])[0]
            top_indices = np.argsort(scores)[::-1][:10]

            for idx_i in top_indices:
                score = float(scores[idx_i])
                if score < 0.4:
                    continue
                cat_id = index['ids'][idx_i]
                if cat_id not in matches:
                    matches[cat_id] = {
                        'id': cat_id, 'name': index['names'][idx_i],
                        'score': score, 'hs_code': index['hs_codes'][idx_i],
                        'method': 'semantic', 'matched_variants': [],
                    }

        # Fuzzy variant matching
        try:
            matched_subcat_ids = list(matches.keys())
            if matched_subcat_ids:
                candidate_items = ProductItem.objects.filter(
                    sub_category_id__in=matched_subcat_ids
                ).values('id', 'name', 'sub_category_id')
                for item in candidate_items:
                    parent_id = item['sub_category_id']
                    if item['id'] in matches[parent_id].get('matched_variants', []):
                        continue
                    ratio = SequenceMatcher(None, clean_qs, item['name'].lower()).ratio()
                    if ratio > 0.85:
                        if 'matched_variants' not in matches[parent_id]:
                            matches[parent_id]['matched_variants'] = []
                        matches[parent_id]['matched_variants'].append(item['id'])
        except Exception as e:
            logger.warning(f"Fuzzy match error: {e}")

        results = list(matches.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def _clean_query(self, query: str) -> str:
        stopwords = ['i', 'want', 'to', 'buy', 'suppliers', 'sell', 'who',
                     'sells', 'find', 'search', 'for', 'please', 'looking']
        words = query.lower().split()
        return ' '.join(w for w in words if w not in stopwords)
