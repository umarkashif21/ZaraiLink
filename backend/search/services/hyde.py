"""
backend/search/services/hyde.py

HyDE (Hypothetical Document Embeddings) for short F1 discovery queries.

Problem: Short queries like "sugar" or "dextrose" don't embed well — the query
vector is too generic to retrieve specific subcategories via FAISS.

Solution: Generate a hypothetical supplier profile that an ideal result would have,
then embed THAT text. Blend the query embedding with the hypothetical embedding.

  final_vec = 0.5 * query_vec + 0.5 * hyde_vec  (then L2-normalize)

Model:
  - GPT-4o-mini via OpenAI API (if OPENAI_API_KEY is set)
  - Template-based profile generator (fallback, no API key needed)

Apply only when:
  - family == 1 (generic discovery, no structural constraints)
  - query has ≤ 4 words (short queries benefit most)
  - dense recall signal is low (guard against applying when retrieval is already good)

Feature flag: SEARCH_USE_HYDE in settings.py (default True)
Cache: simple in-memory dict (query_text → hypothetical_text) to avoid repeat LLM calls
"""

import re
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------
HYDE_MAX_QUERY_WORDS = 4    # only apply to short (≤4 word) queries
HYDE_BLEND_ALPHA = 0.5      # weight of HyDE vector in blend
HYDE_FAMILY = 1             # only apply to F1 generic discovery

_HYDE_PROMPT = (
    "Generate a brief supplier profile (2-3 sentences) for a company that would be "
    "the ideal result for this trade query: '{query}'. "
    "Include: company type, products they supply, countries they operate in, "
    "typical trade volumes in metric tons."
)


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------
_expander_instance: Optional['HyDEExpander'] = None


def get_hyde_expander() -> 'HyDEExpander':
    global _expander_instance
    if _expander_instance is None:
        _expander_instance = HyDEExpander()
    return _expander_instance


# -----------------------------------------------------------------------
# HyDEExpander
# -----------------------------------------------------------------------

class HyDEExpander:
    """
    Generates and encodes hypothetical supplier profiles for short F1 queries.

    Usage:
        expander = HyDEExpander()
        hyp_vec = expander.expand(query, family=1, query_vec=query_embedding)
        # Returns blended embedding or original query_vec if HyDE is skipped
    """

    def __init__(self):
        self._cache: dict = {}          # query_text → hypothetical_text
        self._openai_available: Optional[bool] = None

    def _check_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        if self._openai_available is None:
            import os
            key = os.environ.get('OPENAI_API_KEY', '')
            self._openai_available = bool(key)
        return self._openai_available

    # ------------------------------------------------------------------

    def generate_hypothetical_profile(self, query: str) -> str:
        """
        Generate a hypothetical supplier profile for the query.

        Uses GPT-4o-mini if available, otherwise a template-based generator.

        Returns:
            A 2-3 sentence profile string.
        """
        # Check cache first
        if query in self._cache:
            return self._cache[query]

        if self._check_openai():
            text = self._gpt_profile(query)
        else:
            text = self._template_profile(query)

        self._cache[query] = text
        return text

    def _gpt_profile(self, query: str) -> str:
        """Call GPT-4o-mini to generate hypothetical profile."""
        try:
            import os
            from openai import OpenAI
            client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{
                    "role": "user",
                    "content": _HYDE_PROMPT.format(query=query),
                }],
                temperature=0.7,
                max_tokens=150,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"HyDE GPT call failed: {e}, falling back to template")
            return self._template_profile(query)

    def _template_profile(self, query: str) -> str:
        """
        Template-based hypothetical profile (no LLM needed).

        Generates a plausible supplier description using the query terms
        and common trade domain context.
        """
        clean = re.sub(r'[^\w\s]', '', query).strip()
        return (
            f"A leading international supplier of {clean} products, exporting to Pakistan "
            f"and other Asian markets. Specializes in pharmaceutical and food-grade {clean}, "
            f"with typical shipment volumes of 100-5000 metric tons per order from facilities "
            f"in China, India, and Europe."
        )

    # ------------------------------------------------------------------

    def encode_hypothetical(self, hypothetical_text: str) -> Optional[np.ndarray]:
        """
        Encode the hypothetical profile using nomic-embed-text-v1.

        Uses "search_document: " prefix as required by nomic.
        Returns 768-dim normalized embedding or None on failure.
        """
        try:
            from search.services.retrieval import get_embedding_model, DOC_PREFIX
            model, model_name = get_embedding_model()
            prefix = DOC_PREFIX if model_name == 'nomic' else ''
            vec = model.encode([prefix + hypothetical_text], normalize_embeddings=True)[0]
            return vec.astype(np.float32)
        except Exception as e:
            logger.warning(f"HyDE encoding failed: {e}")
            return None

    # ------------------------------------------------------------------

    def expand(
        self,
        query: str,
        family: int,
        query_vec: Optional[np.ndarray] = None,
    ) -> tuple[Optional[np.ndarray], bool]:
        """
        Expand a query with a hypothetical document embedding.

        Args:
            query:      original query string
            family:     parsed query family (F1-F9)
            query_vec:  original query embedding (768-dim); if None, returns (None, False)

        Returns:
            (blended_vec, hyde_used): blended embedding and whether HyDE was applied.
            If HyDE is skipped, returns (query_vec, False).
        """
        # Guard: only apply to short F1 queries
        if family != HYDE_FAMILY:
            return query_vec, False

        word_count = len(query.strip().split())
        if word_count > HYDE_MAX_QUERY_WORDS:
            return query_vec, False

        if query_vec is None:
            return None, False

        try:
            # Generate hypothetical profile
            hypothetical = self.generate_hypothetical_profile(query)

            # Encode it
            hyde_vec = self.encode_hypothetical(hypothetical)
            if hyde_vec is None:
                return query_vec, False

            if hyde_vec.shape != query_vec.shape:
                logger.warning(f"HyDE vector shape mismatch: {hyde_vec.shape} vs {query_vec.shape}")
                return query_vec, False

            # Blend and normalize
            blended = HYDE_BLEND_ALPHA * query_vec + (1.0 - HYDE_BLEND_ALPHA) * hyde_vec
            norm = np.linalg.norm(blended)
            if norm > 0:
                blended = blended / norm

            logger.debug(f"HyDE applied for query={query!r}")
            return blended.astype(np.float32), True

        except Exception as e:
            logger.warning(f"HyDE expansion failed: {e}")
            return query_vec, False
