"""
backend/search/services/retrieval.py

Hybrid BM25 + FAISS-HNSW + Reciprocal Rank Fusion (RRF) retrieval layer.

Replaces the brute-force cosine similarity in nlp.py with:
  1. BM25 (rank_bm25) over ProductSubCategory names + synonyms + HS codes
  2. FAISS HNSW (nomic-embed-text-v1, 768-dim) for semantic recall
  3. RRF (k=60) to merge ranked lists without score normalization issues

nomic-embed-text-v1 requires task-type prefixes:
  - Index documents: "search_document: <text>"
  - Query encoding: "search_query: <text>"

Index is persisted to FAISS_INDEX_PATH as a pickle (.pkl) alongside the
existing search_index.pkl to maintain backward compatibility.
"""

import os
import re
import pickle
import logging
import numpy as np
from functools import lru_cache
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

FAISS_INDEX_PATH = os.path.join(settings.BASE_DIR, 'search_index_v2.pkl')
RRF_K = 60  # RRF rank bias constant
TOP_BM25 = 20
TOP_FAISS = 20
MIN_BM25_SCORE = 0.1  # relative to max BM25 score
MIN_FAISS_SCORE = 0.35  # cosine similarity threshold

# nomic-embed-text task prefixes
QUERY_PREFIX = 'search_query: '
DOC_PREFIX = 'search_document: '


# ---------------------------------------------------------------------------
# Model singletons
# ---------------------------------------------------------------------------

class _NomicModel:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            logger.info("Loading nomic-embed-text-v1...")
            from sentence_transformers import SentenceTransformer
            cls._instance = SentenceTransformer(
                'nomic-ai/nomic-embed-text-v1',
                trust_remote_code=True,
                device='cpu',
                model_kwargs={'low_cpu_mem_usage': False},
            )
            logger.info(f"nomic-embed-text-v1 loaded (dim={cls._instance.get_sentence_embedding_dimension()})")
        return cls._instance


class _MiniLMModel:
    """Fallback model — used if nomic is unavailable."""
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            from sentence_transformers import SentenceTransformer
            cls._instance = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device='cpu',
                model_kwargs={'low_cpu_mem_usage': False},
            )
        return cls._instance


def get_embedding_model():
    """Get embedding model, preferring nomic-embed-text-v1."""
    try:
        return _NomicModel.get(), 'nomic'
    except Exception as e:
        logger.warning(f"nomic-embed-text-v1 unavailable ({e}), falling back to all-MiniLM-L6-v2")
        return _MiniLMModel.get(), 'minilm'


# ---------------------------------------------------------------------------
# Text preparation
# ---------------------------------------------------------------------------

def _build_document_text(name: str, hs_code: str, synonyms: list[str] = None) -> str:
    """Build the full document text for a ProductSubCategory index entry."""
    parts = [name, hs_code or '']
    if synonyms:
        parts.extend(synonyms)
    return ' '.join(filter(None, parts))


def _tokenise(text: str) -> list[str]:
    """Simple whitespace + lowercase tokeniser for BM25."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.split()


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------

def build_index(force_rebuild: bool = False) -> dict:
    """
    Build (or load from cache) the combined BM25 + FAISS index.

    Returns:
        index dict:
          ids:       list[int]      SubCategory IDs
          names:     list[str]      SubCategory names
          hs_codes:  list[str]      HS codes
          bm25:      BM25Okapi      fitted BM25 index
          faiss_idx: faiss.Index    HNSW index
          embeddings: np.ndarray   (n, dim) nomic embeddings (kept for RRF)
          model_name: str           'nomic' or 'minilm'
          embedding_dim: int
    """
    if not force_rebuild and os.path.exists(FAISS_INDEX_PATH):
        try:
            with open(FAISS_INDEX_PATH, 'rb') as f:
                idx = pickle.load(f)
            logger.info(
                f"Loaded index v2: {len(idx['ids'])} subcategories, "
                f"model={idx.get('model_name', 'unknown')}"
            )
            return idx
        except Exception as e:
            logger.warning(f"Failed to load index v2, rebuilding: {e}")

    logger.info("Building hybrid BM25 + FAISS index...")
    return _rebuild_index()


def _rebuild_index() -> dict:
    """Rebuild the index from scratch using the database."""
    from trade_data.models import ProductSubCategory, ProductItem
    import faiss
    from rank_bm25 import BM25Okapi

    # Fetch all subcategories
    subcats = list(ProductSubCategory.objects.select_related().all())
    if not subcats:
        raise ValueError("No ProductSubCategory records found — cannot build index")

    ids = []
    names = []
    hs_codes = []
    documents = []  # full text for BM25 + embedding

    for sc in subcats:
        # Get all item names for this subcategory (expand vocabulary)
        item_names = list(
            ProductItem.objects.filter(sub_category=sc).values_list('name', flat=True)[:5]
        )
        doc_text = _build_document_text(sc.name, sc.hs_code, item_names)

        ids.append(sc.id)
        names.append(sc.name)
        hs_codes.append(sc.hs_code or '')
        documents.append(doc_text)

    n = len(ids)
    logger.info(f"  Building BM25 over {n} documents...")

    # BM25
    tokenised = [_tokenise(doc) for doc in documents]
    bm25 = BM25Okapi(tokenised)

    # Embeddings
    logger.info(f"  Building embeddings ({n} docs)...")
    model, model_name = get_embedding_model()
    dim = model.get_sentence_embedding_dimension()

    # Prefix for nomic document encoding
    prefix = DOC_PREFIX if model_name == 'nomic' else ''
    prefixed_docs = [prefix + doc for doc in documents]

    embeddings = model.encode(
        prefixed_docs,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = embeddings.astype(np.float32)

    # FAISS HNSW index (M=32 for balance of speed/recall)
    logger.info(f"  Building FAISS HNSW (dim={dim}, n={n})...")
    faiss_idx = faiss.IndexHNSWFlat(dim, 32)
    faiss_idx.hnsw.efConstruction = 200
    faiss_idx.hnsw.efSearch = 50
    faiss_idx.add(embeddings)

    idx = {
        'ids': ids,
        'names': names,
        'hs_codes': hs_codes,
        'documents': documents,
        'bm25': bm25,
        'faiss_idx': faiss_idx,
        'embeddings': embeddings,  # kept for RRF + fallback
        'model_name': model_name,
        'embedding_dim': dim,
        'n_docs': n,
    }

    # Persist
    with open(FAISS_INDEX_PATH, 'wb') as f:
        pickle.dump(idx, f, protocol=4)

    logger.info(f"  Index built and saved to {FAISS_INDEX_PATH}")
    return idx


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class HybridRetriever:
    """
    BM25 + FAISS-HNSW + RRF hybrid retriever for ProductSubCategory matching.

    Thread-safe: uses class-level singleton index.
    """

    _index: Optional[dict] = None

    @classmethod
    def get_index(cls) -> dict:
        if cls._index is None:
            cls._index = build_index()
        return cls._index

    @classmethod
    def invalidate_index(cls):
        cls._index = None
        if os.path.exists(FAISS_INDEX_PATH):
            os.remove(FAISS_INDEX_PATH)
        logger.info("Index invalidated. Will rebuild on next query.")

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.5,
        faiss_weight: float = 0.5,
        family: int = 1,
    ) -> list[dict]:
        """
        Retrieve top-k matching ProductSubCategories for a query.

        Returns list of dicts:
          {id, name, hs_code, score, method, bm25_rank, faiss_rank}
        sorted by descending RRF score.
        """
        idx = self.get_index()
        clean_q = _clean_query(query)

        if not clean_q:
            return []

        # 1. BM25 retrieval
        bm25_results = self._bm25_retrieve(clean_q, idx, TOP_BM25)

        # 2. FAISS retrieval
        faiss_results = self._faiss_retrieve(clean_q, idx, TOP_FAISS, family=family)

        # 3. Keyword exact match (preserves high-precision keyword hits)
        keyword_results = self._keyword_retrieve(clean_q, idx)

        # 3b. Fuzzy fallback for partial/misspelled words (fires when
        #     BM25 and keyword both return nothing — e.g. "sug", "suag", "dextroze")
        fuzzy_results = {}
        if not bm25_results and not keyword_results and len(clean_q) >= 2:
            fuzzy_results = self._fuzzy_retrieve(clean_q, idx, top_k=TOP_BM25)

        # 4. RRF fusion
        rrf_scores = self._rrf_fuse(
            [bm25_results, faiss_results, keyword_results, fuzzy_results],
            k=RRF_K,
        )

        # 4b. Exact-match boost: if keyword returned an exact match (score=1.0),
        # multiply its RRF score by 20 so it always ranks above substring matches.
        # Also add a HS-code match boost if query looks like an HS code.
        exact_ids = {cid for cid, info in keyword_results.items() if info['score'] >= 1.0}
        for cid in exact_ids:
            if cid in rrf_scores:
                rrf_scores[cid] *= 20.0
            else:
                # Ensure exact-matched ID appears in results even if not in BM25/FAISS
                rrf_scores[cid] = 20.0 / (RRF_K + 1)

        # HS-code direct lookup
        if re.match(r'^\d{4}[\.\d]*$', clean_q.strip()):
            hs_ids = self._hs_code_retrieve(clean_q.strip(), idx)
            for cid, info in hs_ids.items():
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 15.0 / (RRF_K + info['rank'])

        # 5. Build result list
        results = []
        id_to_idx = {cid: i for i, cid in enumerate(idx['ids'])}

        for cat_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            i = id_to_idx.get(cat_id)
            if i is None:
                continue

            # Determine primary method
            method = 'rrf'
            if cat_id in keyword_results:
                method = 'keyword'
            elif cat_id in bm25_results and bm25_results[cat_id]['rank'] <= 3:
                method = 'bm25'
            elif cat_id in faiss_results and faiss_results[cat_id]['rank'] <= 3:
                method = 'semantic'

            results.append({
                'id': cat_id,
                'name': idx['names'][i],
                'hs_code': idx['hs_codes'][i],
                'score': round(rrf_score, 6),
                'method': method,
                'bm25_rank': bm25_results.get(cat_id, {}).get('rank'),
                'faiss_rank': faiss_results.get(cat_id, {}).get('rank'),
                'matched_variants': [],  # populated later if needed
            })

        return results

    def _bm25_retrieve(self, query: str, idx: dict, top_k: int) -> dict[int, dict]:
        """BM25 retrieval. Returns {cat_id: {rank, score}}."""
        tokens = _tokenise(query)
        scores = idx['bm25'].get_scores(tokens)

        max_score = scores.max() if len(scores) > 0 else 1.0
        if max_score <= 0:
            return {}

        # Get top_k by score
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = {}
        rank = 1
        for i in top_indices:
            rel_score = float(scores[i]) / max_score
            if rel_score < MIN_BM25_SCORE:
                break
            cat_id = idx['ids'][i]
            results[cat_id] = {'rank': rank, 'score': float(scores[i])}
            rank += 1

        return results

    def _faiss_retrieve(self, query: str, idx: dict, top_k: int, family: int = 1) -> dict[int, dict]:
        """FAISS HNSW retrieval. Returns {cat_id: {rank, score}}."""
        model, model_name = get_embedding_model()
        prefix = QUERY_PREFIX if model_name == 'nomic' else ''

        query_vec = model.encode(
            [prefix + query],
            normalize_embeddings=True,
        ).astype(np.float32)

        # Phase 4-B: HyDE expansion for short F1 queries
        try:
            from django.conf import settings as _s
            if getattr(_s, 'SEARCH_USE_HYDE', True):
                from search.services.hyde import get_hyde_expander
                expander = get_hyde_expander()
                blended_vec, hyde_used = expander.expand(query, family=family, query_vec=query_vec[0])
                if hyde_used and blended_vec is not None:
                    query_vec = blended_vec.reshape(1, -1)
        except Exception:
            pass  # HyDE failure must never break retrieval

        # Search FAISS index
        distances, faiss_indices = idx['faiss_idx'].search(query_vec, top_k)

        results = {}
        for rank, (dist, fi) in enumerate(zip(distances[0], faiss_indices[0])):
            if fi < 0:  # FAISS returns -1 for not-found
                continue
            # For IndexHNSWFlat with normalized vectors, dist = cosine distance (1 - similarity)
            # Actual cosine similarity = 1 - dist when vectors are L2-normalized
            cosine_sim = float(1.0 - dist) if dist <= 1.0 else float(dist)

            if cosine_sim < MIN_FAISS_SCORE:
                break
            cat_id = idx['ids'][fi]
            results[cat_id] = {'rank': rank + 1, 'score': cosine_sim}

        return results

    def _keyword_retrieve(self, query: str, idx: dict) -> dict[int, dict]:
        """
        Exact substring match for high-precision boosting.
        Results sorted by match quality: shorter names = more specific = higher rank.
        Returns {cat_id: {rank, score}}.
        """
        from trade_data.models import ProductSubCategory, ProductItem

        query_lower = query.lower()
        candidates = []

        # SubCategory name contains query
        subcat_hits = list(ProductSubCategory.objects.filter(name__icontains=query))
        for hit in subcat_hits:
            name_lower = hit.name.lower()
            # Score: exact match > near-exact > substring
            if name_lower == query_lower:
                match_score = 1.0
            elif name_lower.startswith(query_lower) or query_lower.startswith(name_lower):
                match_score = 0.98
            else:
                # Reward shorter names (more specific) — normalized by length ratio
                match_score = 0.95 * min(len(query_lower), len(name_lower)) / max(len(query_lower), len(name_lower))
            candidates.append((match_score, hit.id))

        # ProductItem name contains query → boost parent SubCategory
        item_hits = list(ProductItem.objects.filter(
            name__icontains=query
        ).select_related('sub_category'))
        seen_parents = {c[1] for c in candidates}
        for item in item_hits:
            parent_id = item.sub_category_id
            if parent_id in seen_parents:
                continue
            name_lower = item.name.lower()
            match_score = 0.90 * min(len(query_lower), len(name_lower)) / max(len(query_lower), len(name_lower))
            candidates.append((match_score, parent_id))
            seen_parents.add(parent_id)

        # Sort by match score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        matches = {}
        for rank, (score, cat_id) in enumerate(candidates):
            matches[cat_id] = {'rank': rank + 1, 'score': score}

        return matches

    def _fuzzy_retrieve(self, query: str, idx: dict, top_k: int = 10) -> dict[int, dict]:
        """
        Character-level fuzzy matching for typos and partial words.

        Uses trigram prefix overlap + Damerau-Levenshtein similarity
        to find product names that are close to the query token.
        Fires only when query is short (<=12 chars) or looks like a partial word.

        Returns {cat_id: {rank, score}}.
        """
        from trade_data.models import ProductSubCategory
        query_lower = query.lower().strip()
        if not query_lower or len(query_lower) < 2:
            return {}

        # Build trigram set for query
        def trigrams(s):
            s = f' {s} '
            return {s[i:i+3] for i in range(len(s)-2)}

        q_tris = trigrams(query_lower)
        if not q_tris:
            return {}

        def edit_distance(a, b):
            """Simple Levenshtein distance."""
            if a == b: return 0
            if not a: return len(b)
            if not b: return len(a)
            d = list(range(len(b)+1))
            for i, ca in enumerate(a):
                d2 = [i+1]
                for j, cb in enumerate(b):
                    cost = 0 if ca == cb else 1
                    d2.append(min(d2[-1]+1, d[j+1]+1, d[j]+cost))
                d = d2
            return d[-1]

        candidates = []
        for sc in ProductSubCategory.objects.all():
            name_lower = sc.name.lower()
            best_score = 0.0
            for token in name_lower.split():
                if len(token) < 2:
                    continue
                t_tris = trigrams(token)
                union = q_tris | t_tris
                jaccard = len(q_tris & t_tris) / len(union) if union else 0
                prefix_bonus = 0.3 if token.startswith(query_lower) else 0.0
                trigram_score = jaccard + prefix_bonus

                # Edit distance fallback for short tokens (catches transpositions like suag→sugar)
                edit_score = 0.0
                if len(query_lower) >= 3 and len(token) <= len(query_lower) + 3:
                    dist = edit_distance(query_lower, token[:len(query_lower)+2])
                    max_len = max(len(query_lower), len(token))
                    edit_score = max(0, 1.0 - dist / max_len) * 0.6  # cap at 0.6

                score = max(trigram_score, edit_score)
                if score > best_score:
                    best_score = score

            if best_score > 0.25:
                candidates.append((best_score, sc.id))

        candidates.sort(key=lambda x: -x[0])
        return {cat_id: {'rank': i+1, 'score': score}
                for i, (score, cat_id) in enumerate(candidates[:top_k])}

    def _hs_code_retrieve(self, hs_query: str, idx: dict) -> dict[int, dict]:
        """Look up subcategories by HS code prefix match."""
        from trade_data.models import ProductSubCategory

        hits = list(ProductSubCategory.objects.filter(hs_code__startswith=hs_query))
        results = {}
        for rank, hit in enumerate(hits):
            # Exact prefix match
            results[hit.id] = {'rank': rank + 1, 'score': 1.0}
        return results

    def _rrf_fuse(
        self,
        ranked_lists: list[dict[int, dict]],
        k: int = 60,
    ) -> dict[int, float]:
        """
        Reciprocal Rank Fusion.

        RRF_score(d) = Σ_i 1 / (k + rank_i(d))

        If a document is not in a ranked list, it contributes 0 to that list's term.
        """
        scores: dict[int, float] = {}

        for ranked in ranked_lists:
            for cat_id, info in ranked.items():
                r = info['rank']
                contrib = 1.0 / (k + r)
                scores[cat_id] = scores.get(cat_id, 0.0) + contrib

        return scores


# ---------------------------------------------------------------------------
# Convenience function (drop-in for nlp.py)
# ---------------------------------------------------------------------------

_retriever: Optional[HybridRetriever] = None


def hybrid_match(query: str, top_k: int = 10) -> list[dict]:
    """
    Drop-in replacement for QueryMatcher.match() that uses hybrid BM25+FAISS+RRF.
    """
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever.retrieve(query, top_k=top_k)


def _clean_query(query: str) -> str:
    """Remove common intent noise words to get the product term."""
    stopwords = {
        'i', 'want', 'to', 'buy', 'suppliers', 'seller', 'sellers', 'sell',
        'who', 'sells', 'find', 'search', 'for', 'please', 'looking',
        'exporters', 'exporter', 'importers', 'importer', 'buyers', 'buyer',
        'top', 'best', 'rank', 'compare', 'which', 'countries', 'country',
        'from', 'in', 'the', 'a', 'an', 'of', 'and', 'or',
        'supplier', 'supply', 'recent', 'latest', 'last', 'months', 'year',
        'under', 'above', 'below', 'mt', 'kg', 'ton', 'tons', 'metric',
        'per', 'shipments', 'transactions', 'history',
    }
    words = query.lower().split()
    clean = []
    for w in words:
        if w in stopwords:
            continue
        # Preserve HS-code-like tokens (e.g. "1702.111", "1704.909")
        is_hs_code = bool(re.match(r'^\d{4}[\.\d]*$', w))
        # Preserve plain integers only if they look like HS codes
        is_plain_int = w.replace(',', '').isdigit() and len(w) <= 4
        if is_hs_code or not (w.replace('.', '').replace('/', '').replace(',', '').isdigit()):
            clean.append(w)
    return ' '.join(clean).strip()
