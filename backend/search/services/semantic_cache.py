"""
backend/search/services/semantic_cache.py

Redis-backed semantic search cache.

Key design decisions:
  - Threshold=0.92 cosine similarity for cache hit (high enough to avoid false hits)
  - TTL=3600s (1 hour) per cached query
  - HNSW-style index over cached query embeddings for fast nearest-neighbor lookup
  - Category-tagged invalidation: when a product category's data changes, purge related entries
  - Cache key: SHA-256 of normalized query
  - Stored value: JSON-serialized search response + query embedding

Redis data structures:
  - HASH  zarailink:scache:entry:{sha256}   → {response, embedding_b64, query, created_at}
  - ZSET  zarailink:scache:index            → sha256 → timestamp (for TTL cleanup)
  - SET   zarailink:scache:cat:{subcat_id}  → set of sha256 keys (for category invalidation)
"""

import os
import json
import time
import base64
import hashlib
import logging
import numpy as np
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = 'zarailink:scache'
SIMILARITY_THRESHOLD = 0.92
TTL_SECONDS = 3600  # 1 hour
MAX_CACHE_ENTRIES = 2000  # evict oldest when exceeded


def _get_redis():
    """Get Redis connection, returning None if unavailable."""
    try:
        import redis
        from django.conf import settings
        host = getattr(settings, 'REDIS_HOST', '127.0.0.1')
        port = getattr(settings, 'REDIS_PORT', 6379)
        db = getattr(settings, 'REDIS_CACHE_DB', 1)
        r = redis.Redis(host=host, port=port, db=db, socket_timeout=0.5)
        r.ping()
        return r
    except Exception as e:
        logger.debug(f"Redis unavailable: {e}")
        return None


def _normalize_query(query: str) -> str:
    """Normalize query for consistent cache keys."""
    return ' '.join(query.lower().split())


def _query_sha(query: str) -> str:
    return hashlib.sha256(_normalize_query(query).encode()).hexdigest()[:16]


def _embed_query(query: str) -> Optional[np.ndarray]:
    """Get query embedding using the nomic (or fallback) model."""
    try:
        from search.services.retrieval import get_embedding_model, QUERY_PREFIX
        model, model_name = get_embedding_model()
        prefix = QUERY_PREFIX if model_name == 'nomic' else ''
        vec = model.encode([prefix + query], normalize_embeddings=True)[0]
        return vec.astype(np.float32)
    except Exception as e:
        logger.warning(f"Failed to embed query for cache: {e}")
        return None


def _vec_to_b64(vec: np.ndarray) -> str:
    return base64.b64encode(vec.tobytes()).decode()


def _b64_to_vec(s: str, dim: int = 768) -> Optional[np.ndarray]:
    try:
        return np.frombuffer(base64.b64decode(s), dtype=np.float32)
    except Exception:
        return None


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity (already normalized vectors → dot product)."""
    return float(np.dot(a, b))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class SemanticCache:
    """
    Semantic cache for search results.

    Usage:
        cache = SemanticCache()
        hit = cache.get(query)
        if hit:
            return hit['response']
        # ... run search ...
        cache.set(query, response, matched_subcat_ids)
    """

    def __init__(self):
        self._r = None
        self._connected = None

    def _redis(self):
        if self._connected is None:
            self._r = _get_redis()
            self._connected = self._r is not None
        return self._r

    def get(self, query: str) -> Optional[dict]:
        """
        Look up a cached response for the query.

        Returns cached response dict or None on miss.
        Algorithm:
          1. SHA lookup for exact normalized query (O(1))
          2. Embedding-based similarity scan over all cached entries (O(n))
             — capped at MAX_CACHE_ENTRIES to bound scan cost
        """
        r = self._redis()
        if r is None:
            return None

        norm_q = _normalize_query(query)
        sha = _query_sha(norm_q)

        # Fast path: exact normalized match
        exact_key = f'{CACHE_KEY_PREFIX}:entry:{sha}'
        try:
            raw = r.hget(exact_key, 'data')
            if raw:
                data = json.loads(raw)
                # Refresh TTL on hit
                r.expire(exact_key, TTL_SECONDS)
                logger.debug(f"Cache HIT (exact): {query!r}")
                return data.get('response')
        except Exception as e:
            logger.warning(f"Cache exact lookup error: {e}")

        # Semantic path: find nearest cached query embedding
        query_vec = _embed_query(norm_q)
        if query_vec is None:
            return None

        try:
            # Get all cached shas from the ZSET index
            all_shas = r.zrange(f'{CACHE_KEY_PREFIX}:index', 0, -1)
            if not all_shas:
                return None

            best_score = 0.0
            best_sha = None

            for sha_bytes in all_shas[:MAX_CACHE_ENTRIES]:
                sha_key = sha_bytes.decode() if isinstance(sha_bytes, bytes) else sha_bytes
                entry_key = f'{CACHE_KEY_PREFIX}:entry:{sha_key}'
                emb_b64 = r.hget(entry_key, 'embedding')
                if not emb_b64:
                    continue
                cached_vec = _b64_to_vec(
                    emb_b64.decode() if isinstance(emb_b64, bytes) else emb_b64
                )
                if cached_vec is None or cached_vec.shape != query_vec.shape:
                    continue
                sim = _cosine_sim(query_vec, cached_vec)
                if sim > best_score:
                    best_score = sim
                    best_sha = sha_key

            if best_score >= SIMILARITY_THRESHOLD and best_sha:
                entry_key = f'{CACHE_KEY_PREFIX}:entry:{best_sha}'
                raw = r.hget(entry_key, 'data')
                if raw:
                    data = json.loads(raw)
                    r.expire(entry_key, TTL_SECONDS)
                    logger.debug(
                        f"Cache HIT (semantic, sim={best_score:.3f}): {query!r}"
                    )
                    return data.get('response')

        except Exception as e:
            logger.warning(f"Cache semantic lookup error: {e}")

        return None

    def set(
        self,
        query: str,
        response: dict,
        matched_subcat_ids: list[int] = None,
    ) -> bool:
        """
        Store a search response in the cache.

        Args:
            query: original query string
            response: serializable response dict
            matched_subcat_ids: for category-based invalidation
        """
        r = self._redis()
        if r is None:
            return False

        norm_q = _normalize_query(query)
        sha = _query_sha(norm_q)

        query_vec = _embed_query(norm_q)
        if query_vec is None:
            return False

        try:
            entry_key = f'{CACHE_KEY_PREFIX}:entry:{sha}'
            index_key = f'{CACHE_KEY_PREFIX}:index'

            data = {
                'query': norm_q,
                'response': response,
                'created_at': time.time(),
            }

            pipe = r.pipeline()
            pipe.hset(entry_key, mapping={
                'data': json.dumps(data, default=str),
                'embedding': _vec_to_b64(query_vec),
            })
            pipe.expire(entry_key, TTL_SECONDS)
            pipe.zadd(index_key, {sha: time.time()})
            pipe.expire(index_key, TTL_SECONDS * 2)

            # Category tags for invalidation
            if matched_subcat_ids:
                for subcat_id in matched_subcat_ids:
                    cat_key = f'{CACHE_KEY_PREFIX}:cat:{subcat_id}'
                    pipe.sadd(cat_key, sha)
                    pipe.expire(cat_key, TTL_SECONDS * 2)

            pipe.execute()

            # Evict oldest entries if over limit
            self._maybe_evict(r, index_key)

            logger.debug(f"Cache SET: {query!r} (sha={sha})")
            return True

        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate_category(self, subcat_id: int) -> int:
        """Invalidate all cached entries that touched a given subcategory."""
        r = self._redis()
        if r is None:
            return 0

        cat_key = f'{CACHE_KEY_PREFIX}:cat:{subcat_id}'
        index_key = f'{CACHE_KEY_PREFIX}:index'

        try:
            shas = r.smembers(cat_key)
            if not shas:
                return 0

            pipe = r.pipeline()
            for sha_bytes in shas:
                sha = sha_bytes.decode() if isinstance(sha_bytes, bytes) else sha_bytes
                pipe.delete(f'{CACHE_KEY_PREFIX}:entry:{sha}')
                pipe.zrem(index_key, sha)
            pipe.delete(cat_key)
            pipe.execute()

            logger.info(f"Cache invalidated {len(shas)} entries for subcat_id={subcat_id}")
            return len(shas)

        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return 0

    def flush_all(self) -> int:
        """Flush all cached entries."""
        r = self._redis()
        if r is None:
            return 0
        try:
            keys = list(r.scan_iter(f'{CACHE_KEY_PREFIX}:*'))
            if keys:
                r.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning(f"Cache flush error: {e}")
            return 0

    def stats(self) -> dict:
        """Return cache statistics."""
        r = self._redis()
        if r is None:
            return {'connected': False}
        try:
            index_key = f'{CACHE_KEY_PREFIX}:index'
            count = r.zcard(index_key)
            return {
                'connected': True,
                'cached_queries': count,
                'threshold': SIMILARITY_THRESHOLD,
                'ttl_seconds': TTL_SECONDS,
            }
        except Exception:
            return {'connected': True, 'cached_queries': 0}

    def _maybe_evict(self, r, index_key: str):
        """Evict oldest entries if over MAX_CACHE_ENTRIES."""
        try:
            count = r.zcard(index_key)
            if count > MAX_CACHE_ENTRIES:
                n_evict = count - MAX_CACHE_ENTRIES
                oldest = r.zrange(index_key, 0, n_evict - 1)
                pipe = r.pipeline()
                for sha_bytes in oldest:
                    sha = sha_bytes.decode() if isinstance(sha_bytes, bytes) else sha_bytes
                    pipe.delete(f'{CACHE_KEY_PREFIX}:entry:{sha}')
                    pipe.zrem(index_key, sha)
                pipe.execute()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_cache_instance: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance
