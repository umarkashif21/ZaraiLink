"""
nlu_engine.py - Modern NLU Engine (Phase 2)
============================================
SOTA pipeline replacing the legacy DistilBART + BERT-NER + Regex stack.

  Intent   : SetFit  (BAAI/bge-small-en-v1.5 backbone, fine-tuned on trade data)
             Falls back to keyword detection when model not available.
  Entities : GLiNER  (urchade/gliner_base, zero-shot span extraction)
             Falls back gracefully when model not available.
  Keyword  : extract_product_keyword() — fast stop-word stripper (no ML needed)
  Direction: Perspective logic that converts (intent + ui_context) to OpenSearch filters

Public API:
    engine = ModernNLUEngine()
    result = engine.parse(query, ui_context='worldwide')
    # Returns: intent, product, product_keyword, country, price_filter, os_filter

    # Fast keyword extraction (no model needed):
    keyword = extract_product_keyword("i want to buy dextrose anhydrous")
    # → "dextrose anhydrous"
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# BASE_DIR is the backend/ directory (same as Django's settings.BASE_DIR).
# Resolved at import time so it works regardless of how the module is loaded.
_BACKEND_DIR       = Path(__file__).resolve().parent.parent.parent  # backend/
_INTENT_MODEL_PATH = _BACKEND_DIR / "models" / "zarai_intent_model"

# ---------------------------------------------------------------------------
# Price operator keywords → OpenSearch range keys
# ---------------------------------------------------------------------------
_LTE_PHRASES = {"under", "below", "max", "less than", "cheaper than", "at most"}
_GTE_PHRASES = {"above", "over", "min", "more than", "at least", "minimum"}

# ---------------------------------------------------------------------------
# Stop words for product keyword extraction
# These are stripped from the raw query before searching product names.
# Order matters — multi-word phrases first before single words.
# ---------------------------------------------------------------------------
_INTENT_STOP_PHRASES = [
    # Multi-word first
    "i wanna buy", "i wanna sell", "i want to buy", "i want to sell", 
    "i am looking to buy", "i am looking to sell",
    "looking to buy", "looking to sell", "looking for buyers of", "looking for sellers of",
    "looking for suppliers of", "find buyers for", "find sellers for", "find suppliers for",
    "find buyers of", "find sellers of", "find suppliers of",
    "get the product called", "search for", "im looking for", "i am looking for",
    "want to buy", "want to sell", "want to import", "want to export",
    "need to buy", "need to sell", "need to import", "need to export",
    "i need to buy", "i need to sell",
    "where do i get", "where can i buy", "where can i get", "where do i buy",
    "how do i get", "how can i buy", "where to buy", "where to find",
    "who sells", "who buys", "who supplies",
    "suppliers of", "buyers of", "looking for",
    "import of", "export of",
    "i want", "i need", "wanna buy", "wanna sell",
    # Single words last
    "where", "how", "what", "which",
    "buy", "sell", "purchase", "import", "export", "get",
    "supplier", "suppliers", "buyer", "buyers",
    "find", "search", "looking", "please", "need",
    "for", "me", "best",
]


# ===========================================================================
# Public helper — product keyword extraction (no ML, very fast)
# ===========================================================================

def extract_product_keyword(raw_query: str) -> str:
    """
    Strip intent/trade stop-words from a natural-language query and return
    the remaining product-related terms.

    Examples:
        "i want to buy dextrose anhydrous"  → "dextrose anhydrous"
        "find buyers for basmati rice"       → "basmati rice"
        "I WANT TO SELL fruc"               → "fruc"
        "dex"                               → "dex"
        "sugar under $500"                  → "sugar"   (price clause also stripped)
    """
    q = raw_query.lower().strip()

    # Dynamic Stripping of garbled intent verbs (buyyy, gettsds, importttt, etc.)
    # \w* catches ANY junk characters appended to the base word
    q = re.sub(r'\b(buy\w*|sell\w*|get\w*|import\w*|export\w*|purchas\w*|wanna|want\w*)\b', ' ', q)

    # Strip each stop phrase (longest first already, since list is ordered)
    for phrase in _INTENT_STOP_PHRASES:
        # Word-boundary aware replacement
        q = re.sub(r'\b' + re.escape(phrase) + r'\b', ' ', q)

    # Strip price clauses like "under $700", "above 500 usd", "below 300"
    q = re.sub(r'\b(under|below|above|over|min|max|less than|more than|at most|at least)\s*\$?\d+(\s*(usd|pkr|per\s+mt))?\b', '', q)
    q = re.sub(r'\$\d+(\.\d+)?', '', q)   # bare "$500"

    # Strip leftover punctuation / excess whitespace
    q = re.sub(r'[^\w\s]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()

    # Pass 4 Tokenization Fallback:
    # If the remaining string is suspiciously long (e.g. > 4 words), user typed a messy unhandled sentence.
    words = q.split()
    if len(words) > 4:
        # OLD LOGIC: Simple heuristic: filter out short generic words, take the longest remaining word.
        # WHY REPLACED: In a query like "unga bunga dex", it picked "unga" purely due to character length,
        # completely ignoring the actual valid product abbreviation "dex".
        # NEW LOGIC: Score each candidate against our known product catalog using TrigramSimilarity.
        # The word with the highest similarity to any known product wins.
        generic_words = {"the", "a", "an", "is", "of", "and", "or", "to", "in", "from", "on", "with"}
        filtered = [w for w in words if w not in generic_words and len(w) > 2]
        if filtered:
            try:
                import django
                from django.conf import settings
                if not settings.configured:
                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
                    django.setup()
                    
                from trade_data.models import ProductSubCategory, ProductItem
                from django.contrib.postgres.search import TrigramSimilarity
                
                best_word = None
                best_score = 0.0
                
                for candidate in filtered:
                    sc_sim = ProductSubCategory.objects.annotate(
                        sim=TrigramSimilarity('name', candidate)
                    ).order_by('-sim').values_list('sim', flat=True).first() or 0.0
                    
                    it_sim = ProductItem.objects.annotate(
                        sim=TrigramSimilarity('name', candidate)
                    ).order_by('-sim').values_list('sim', flat=True).first() or 0.0
                    
                    max_sim = max(sc_sim, it_sim)
                    
                    if max_sim > best_score:
                        best_score = max_sim
                        best_word = candidate
                        
                if best_word and best_score > 0.1:
                    q = best_word
                else:
                    q = max(filtered, key=len)
            except Exception:
                # Graceful fallback to legacy logic if DB is not ready or errors occur
                q = max(filtered, key=len)

    return q or raw_query.lower().strip()


# ===========================================================================
# Helpers
# ===========================================================================

def _detect_price_operator(query: str) -> Optional[str]:
    """
    Regex fallback to detect a price direction keyword when GLiNER doesn't
    extract a price_operator entity.
    Returns 'lte' or 'gte' or None.
    """
    q = query.lower()
    for phrase in _GTE_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', q):
            return "gte"
    for phrase in _LTE_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', q):
            return "lte"
    return None


def _call_openrouter_llm(system_prompt: str, user_prompt: str) -> Optional[dict]:
    import json
    import requests
    from django.conf import settings

    api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
    if not api_key:
        logger.warning("[LLM] OPENROUTER_API_KEY is missing or empty.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=4)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        logger.warning(f"[LLM] Primary model failed: {e}")
        # Fallback to Mistral Free immediately natively via OpenRouter
        payload["model"] = "mistralai/mistral-7b-instruct:free"
        payload.pop("response_format", None)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=4)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            return json.loads(content)
        except Exception as fallback_e:
            logger.warning(f"[LLM] Fallback model failed: {fallback_e}")
            return None

def _build_price_filter_regex(raw_query: str) -> Optional[dict]:
    """
    Regex-based price extraction — used as fallback when LLM is unavailable.
    Handles: 'under 800', 'cheaper than 800', 'below $500', 'above 1000 usd', 'cheap' (no number).
    """
    q = raw_query.lower()

    # Detect ranking-only signals (cheap/affordable with no number)
    price_ranking_words = {"cheap", "affordable", "budget", "cheapest", "low price", "best price", "inexpensive"}
    has_number = bool(re.search(r'\d', q))
    if not has_number and any(w in q for w in price_ranking_words):
        logger.warning("[RegexPrice] No-number price signal → ranking_hint=price_asc only")
        return {"ranking_hint": "price_asc"}

    # Match patterns like "under 800", "cheaper than $700", "below 500 usd", "above 1000"
    lte_pattern = r'\b(?:under|below|less than|cheaper than|no more than|at most|max)\s*\$?([\d,]+(?:\.\d+)?)'
    gte_pattern = r'\b(?:above|over|more than|at least|minimum|min)\s*\$?([\d,]+(?:\.\d+)?)'
    range_pattern = r'\b(?:around|roughly|approximately|about)\s*\$?([\d,]+(?:\.\d+)?)'

    m = re.search(lte_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        logger.warning(f"[RegexPrice] lte detected: ceiling={val}")
        return {"range": {"usd_per_mt": {"lte": val}}, "ranking_hint": "price_asc"}

    m = re.search(gte_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        logger.warning(f"[RegexPrice] gte detected: floor={val}")
        return {"range": {"usd_per_mt": {"gte": val}}, "ranking_hint": None}

    m = re.search(range_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        tol = 0.15
        logger.warning(f"[RegexPrice] range detected: center={val} tol={tol}")
        return {"range": {"usd_per_mt": {"gte": val * (1 - tol), "lte": val * (1 + tol)}}, "ranking_hint": None}

    return None


_LLM_UNIFIED_PROMPT = '''\
You are a query parser for ZaraiLink, a B2B trade platform connecting Pakistani
and foreign buyers/sellers of physical commodities.

Extract structured information from the user's trade search query.
Return ONLY valid JSON. No explanation, no markdown, no backticks.

Rules:
- product: extract the raw product keyword as the user wrote it, minimal normalization.
  "purchase dex" -> "dex". "I need wheat grain cheap" -> "wheat grain". null if unclear.
  This is used as a search keyword not a display name — keep it close to the original.
- country: full country name if mentioned, null otherwise. Cross-check only —
  do not use this to replace the existing country resolver downstream.
- price.operator: "lte" for max price (under/below/cheap/affordable/at most),
                  "gte" for min price (above/premium/at least), null if none
- price.value: numeric only, null if not mentioned. Written numbers: eight hundred -> 800
- price.currency: "USD" default if price mentioned but currency unclear, null if no price
- price.ranking_hint: "price_asc" if cheapest wanted, "price_desc" if premium, null otherwise
- quantity: raw string as mentioned, null if not mentioned
- On any ambiguity return null, never guess

Return this exact schema:
{
  "product": string | null,
  "country": string | null,
  "price": {
    "operator": "lte" | "gte" | null,
    "value": number | null,
    "currency": string | null,
    "ranking_hint": "price_asc" | "price_desc" | null
  },
  "quantity": string | null
}
'''

_LLM_UNIFIED_EMPTY: dict = {
    "product": None,
    "country": None,
    "price": {"operator": None, "value": None, "currency": None, "ranking_hint": None},
    "quantity": None,
}


def _call_llm_unified(raw_query: str) -> dict:
    """
    Single OpenRouter call that extracts product, country (cross-check),
    price constraints, and quantity together.

    Returns a dict matching _LLM_UNIFIED_EMPTY on any failure — never raises.
    """
    import copy
    try:
        parsed = _call_openrouter_llm(_LLM_UNIFIED_PROMPT, raw_query)
        if not parsed:
            raise ValueError("LLM returned empty result")

        # Ensure the price sub-dict always exists
        result = copy.deepcopy(_LLM_UNIFIED_EMPTY)
        result["product"]  = parsed.get("product") or None
        result["country"]  = parsed.get("country") or None
        result["quantity"] = parsed.get("quantity") or None
        price_raw = parsed.get("price") or {}
        result["price"] = {
            "operator":     price_raw.get("operator"),
            "value":        price_raw.get("value"),
            "currency":     price_raw.get("currency"),
            "ranking_hint": price_raw.get("ranking_hint"),
        }
        logger.debug(f"[LLM] Unified parse succeeded: {result}")
        return result
    except Exception as e:
        logger.warning(f"[LLM] Unified call failed: {e}. Returning empty structure.")
        import copy
        return copy.deepcopy(_LLM_UNIFIED_EMPTY)


def _price_filter_from_llm(llm_result: dict) -> Optional[dict]:
    """
    Convert the price sub-dict from _call_llm_unified into the internal
    price_filter format expected by search_service and aggregation.
    Returns None when no price constraint was found.
    """
    price = llm_result.get("price") or {}
    op    = price.get("operator")
    val   = price.get("value")
    hint  = price.get("ranking_hint")

    if op in ("lte", "gte") and val is not None:
        return {"range": {"usd_per_mt": {op: float(val)}}, "ranking_hint": hint}

    # ranking-only signal (cheap/affordable, no numeric value)
    if hint:
        return {"ranking_hint": hint}

    return None


def _extract_entity(entities: list[dict], label: str) -> Optional[str]:
    """Return the first entity text for a given label, or None."""
    for ent in entities:
        if ent["label"] == label:
            return ent["text"].strip()
    return None


def _build_perspective_filter(
    intent: str,
    ui_context: str,
    country: Optional[str],
) -> dict:
    """
    Maps (intent, ui_context) to OpenSearch bool filter clauses.

    Perspective table:
    ------------------------------------------------------------------
    ui_context  | intent | Meaning
    ------------------------------------------------------------------
    import      | BUY    | Foreign Suppliers
    import      | SELL   | Pakistani Buyers
    export      | BUY    | Pakistani Suppliers
    export      | SELL   | Foreign Buyers
    ------------------------------------------------------------------
    """
    ctx = ui_context.lower()
    must: list[dict] = []

    if ctx == "import":
        must.append({"term": {"trade_type": {"value": "IMPORT", "case_insensitive": True}}})
    elif ctx == "export":
        must.append({"term": {"trade_type": {"value": "EXPORT", "case_insensitive": True}}})

    country_filters = []
    if ctx == "import":
        if intent == "BUY" and country:
            country_filters.append({"term": {"origin_country": {"value": country, "case_insensitive": True}}})
        elif intent == "SELL" and country:
            country_filters.append({"term": {"destination_country": {"value": country, "case_insensitive": True}}})
    elif ctx == "export":
        if intent == "BUY" and country:
            country_filters.append({"term": {"origin_country": {"value": country, "case_insensitive": True}}})
        elif intent == "SELL" and country:
            country_filters.append({"term": {"destination_country": {"value": country, "case_insensitive": True}}})

    result = {}
    if must:
        result["bool"] = {"must": must}
        if country_filters:
            result["bool"]["filter"] = country_filters
    elif country_filters:
        result["bool"] = {"filter": country_filters}

    return result


# ===========================================================================
# ModernNLUEngine
# ===========================================================================

class ModernNLUEngine:
    """
    Phase-4 NLU Engine — SetFit + KeyBERT + GLiNER + RapidFuzz.

    Intent   : SetFit (zarai_intent_model, fine-tuned on trade data).
               Falls back to keyword regex when model not found.
    Keyword  : KeyBERT extracts the best product keyword from the query.
               Falls back to stop-word strip (extract_product_keyword) when
               KeyBERT is unavailable.
    Entities : GLiNER zero-shot NER for country / quantity / price entities.
               Falls back gracefully when model unavailable.
    Country  : RapidFuzz fuzzy match (unchanged).
    Price    : OpenRouter LLM (unchanged).

    All models are loaded lazily at startup and cached as class attributes.
    """

    _intent_model  = None   # SetFit
    _keyword_model = None   # KeyBERT
    _ner_model     = None   # GLiNER

    GLINER_LABELS = [
        "product", "country", "quantity", "unit",
        "price", "currency", "price_operator",
    ]

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    @classmethod
    def _load_intent_model(cls):
        """Load SetFit model from zarai_intent_model/. Silently skips if absent."""
        if cls._intent_model is not None:
            return

        model_path = str(_INTENT_MODEL_PATH.resolve())

        # Accept any of these markers to confirm the model was saved
        markers = ["config_setfit.json", "model_head.pkl", "config.json"]
        model_exists = any(
            os.path.exists(os.path.join(model_path, m)) for m in markers
        )

        if not model_exists:
            logger.warning(
                f"[NLU] SetFit model not found at {model_path}. "
                "Run scripts/train_intent_model.py first. "
                "Falling back to keyword intent detection."
            )
            return

        try:
            from setfit import SetFitModel
            logger.info(f"[NLU] Loading SetFit intent model from {model_path} ...")
            cls._intent_model = SetFitModel.from_pretrained(model_path)
            logger.info("[NLU] SetFit model loaded successfully.")
        except Exception as e:
            logger.error(f"[NLU] Failed to load SetFit model: {e}. Using regex fallback.")

    @classmethod
    def _load_keyword_model(cls):
        """Load KeyBERT using the sentence-transformers backend."""
        if cls._keyword_model is not None:
            return
        try:
            from keybert import KeyBERT
            logger.info("[NLU] Loading KeyBERT model ...")
            cls._keyword_model = KeyBERT(model="paraphrase-MiniLM-L6-v2")
            logger.info("[NLU] KeyBERT loaded.")
        except Exception as e:
            logger.warning(f"[NLU] KeyBERT not available — will use stop-word extraction: {e}")

    @classmethod
    def _load_ner_model(cls):
        """Load GLiNER for entity extraction."""
        if cls._ner_model is not None:
            return
        try:
            from gliner import GLiNER
            logger.info("[NLU] Loading GLiNER model: urchade/gliner_base ...")
            cls._ner_model = GLiNER.from_pretrained("urchade/gliner_base")
            logger.info("[NLU] GLiNER loaded.")
        except Exception as e:
            logger.info(f"[NLU] GLiNER not available — will use keyword product extraction: {e}")

    def __init__(self):
        self._load_intent_model()
        self._load_keyword_model()
        self._load_ner_model()

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------

    def predict_intent(self, query: str) -> str:
        """Returns 'BUY' or 'SELL'.

        Priority order:
          1. SetFit ML model  — most accurate, handles ambiguous phrasing
          2. Keyword regex    — fast fallback when model not loaded
          3. Default to BUY   — safe default
        """
        # 1. SetFit (primary)
        if self._intent_model is not None:
            try:
                pred = self._intent_model.predict([query])[0]
                if isinstance(pred, str):
                    return pred.upper()
                return "BUY" if int(pred) == 0 else "SELL"
            except Exception as e:
                logger.warning(f"[NLU] SetFit inference failed: {e}. Using regex fallback.")

        # 2. Keyword regex fallback
        q = query.lower()
        if re.search(r'\b(sell\w*|export\w*|supply\w*|distribute\w*|buyer\w*)\b', q):
            return "SELL"
        if re.search(r'\b(buy\w*|import\w*|get\w*|purchas\w*|need\w*|supplier\w*)\b', q):
            return "BUY"

        # 3. Default
        return "UNKNOWN"

    # ------------------------------------------------------------------
    # Entity Extraction
    # ------------------------------------------------------------------

    def extract_entities(self, query: str) -> list[dict]:
        """
        Returns a list of dicts: [{"label": "product", "text": "Refined Sugar"}, ...]
        Falls back to empty list when GLiNER not available.
        """
        if self._ner_model is None:
            return []
        try:
            return self._ner_model.predict_entities(
                query, labels=self.GLINER_LABELS, threshold=0.3
            )
        except Exception as e:
            logger.error(f"GLiNER inference error: {e}")
            return []

    # ------------------------------------------------------------------
    # Main public API
    # ------------------------------------------------------------------

    def parse(self, query: str, ui_context: str = "import") -> dict:
        """
        Full NLU parse — 5-step pipeline.

        Returns:
            {
                "intent":          "BUY" | "SELL",
                "product":         str | None,    # best resolved product keyword
                "product_keyword": str,           # alias kept for downstream compat
                "country":         str | None,
                "quantity":        str | None,
                "price_filter":    dict | None,
                "os_filter":       dict,
                "entities":        list[dict],
                "ui_context":      str,
            }
        """
        import time
        t_nlu_total = time.perf_counter()

        # ==================================================================
        # STEP 1 — Intent Detection
        # SetFit model is primary; regex is the fallback.
        # ==================================================================
        t0 = time.perf_counter()
        intent = self.predict_intent(query)
        t_setfit = (time.perf_counter() - t0) * 1000
        logger.info(f"[LATENCY] SetFit: {t_setfit:.0f}ms")
        logger.debug(f"[NLU] Step1 intent={intent!r} query={query!r}")

        # ==================================================================
        # STEP 2 — GLiNER Entity Extraction
        # Extracts country and raw entities. Product from GLiNER is used only
        # as a cross-check, not the primary product keyword.
        # ==================================================================
        entities = self.extract_entities(query)
        gliner_country = (
            _extract_entity(entities, "country")
            or _extract_entity(entities, "location")
        )
        logger.debug(f"[NLU] Step2 gliner_entities={len(entities)} gliner_country={gliner_country!r}")

        # ==================================================================
        # STEP 3 — Country Resolution (RapidFuzz — DO NOT TOUCH)
        # ==================================================================
        t0 = time.perf_counter()
        resolved_country = self._detect_country_fallback(query)
        if not resolved_country and gliner_country:
            resolved_country = self._resolve_country(gliner_country)
        t_rapidfuzz = (time.perf_counter() - t0) * 1000
        logger.info(f"[LATENCY] RapidFuzz: {t_rapidfuzz:.0f}ms")
        logger.debug(f"[NLU] Step3 resolved_country={resolved_country!r}")

        # ==================================================================
        # STEP 4 — Product Keyword Extraction
        # Strip the resolved country so it doesn't pollute keyword scoring.
        # Priority: KeyBERT > LLM cross-check > stop-word strip
        # ==================================================================
        cleaned_query = query
        if resolved_country:
            cleaned_query = re.sub(
                r'\b' + re.escape(resolved_country) + r'\b', ' ',
                cleaned_query, flags=re.IGNORECASE,
            )

        _KB_STOP = [
            "buy", "sell", "purchase", "import", "export",
            "need", "want", "get", "find", "search", "source",
            "supplier", "suppliers", "buyer", "buyers",
            "looking", "require", "required", "seeking",
            "under", "above", "below", "over", "cheap", "cheaper",
            "affordable", "expensive", "price", "rate", "cost",
            "bulk", "urgent", "urgently", "asap", "immediate",
            "ton", "tons", "kg", "mt", "per",
        ]

        product_keyword = None
        product_method  = "none"
        keybert_confidence = 0.0

        t0 = time.perf_counter()
        if self._keyword_model is not None:
            try:
                kw_results = self._keyword_model.extract_keywords(
                    cleaned_query,
                    keyphrase_ngram_range=(1, 2),
                    stop_words=_KB_STOP,
                    top_n=1,
                )
                if kw_results:
                    product_keyword = kw_results[0][0]
                    keybert_confidence = kw_results[0][1]
                    product_method  = "keybert"
            except Exception as e:
                logger.warning(f"[NLU] KeyBERT extraction failed: {e}")

        t_keybert = (time.perf_counter() - t0) * 1000
        logger.info(f"[LATENCY] KeyBERT: {t_keybert:.0f}ms")
        logger.debug(f"[NLU] Step4(keybert) product={product_keyword!r}")

        # ==================================================================
        # STEP 5 — Unified LLM Call (price + quantity + product fallback)
        # One API call extracts everything at once.
        #
        # SKIP LOGIC: We first try to extract prices using our robust regex.
        # If the regex successfully finds a numeric range (or if there's no
        # price complexity at all), we completely skip the 4s OpenRouter call.
        # ==================================================================
        t0 = time.perf_counter()

        has_numbers        = bool(re.search(r'\d', query))
        has_price_operator = _detect_price_operator(query)
        ranking_word_hit   = any(
            w in query.lower()
            for w in {"cheap", "cheapest", "bulk", "premium", "affordable",
                      "best price", "low price", "reliable"}
        )
        
        needs_llm = (has_numbers and has_price_operator) or (has_numbers and ranking_word_hit)
        
        # 1. Try our fast regex first
        regex_price = _build_price_filter_regex(query)
        if regex_price and "range" in regex_price:
            # The regex perfectly extracted the numeric price! No LLM needed.
            needs_llm = False

        price_filter = None
        t_deepseek = 0.0
        
        if not needs_llm:
            logger.warning(
                f"[NLU] Skipping LLM — price handled by regex or not present "
                f"(kb_conf={keybert_confidence:.2f})"
            )
            import copy
            llm_result  = copy.deepcopy(_LLM_UNIFIED_EMPTY)
            price_filter = regex_price # Use the fully built regex price filter
        else:
            llm_result = _call_llm_unified(query)
            t_deepseek = (time.perf_counter() - t0) * 1000
            logger.info(f"[LATENCY] DeepSeek: {t_deepseek:.0f}ms")
            price_filter = _price_filter_from_llm(llm_result)

        quantity     = llm_result.get("quantity")
        llm_product  = llm_result.get("product")

        logger.debug(
            f"[NLU] Step5(llm) product={llm_product!r} "
            f"price_filter={price_filter} quantity={quantity!r}"
        )

        # If KeyBERT returned nothing, use the LLM product
        if not product_keyword and llm_product:
            product_keyword = llm_product
            product_method  = "llm"

        # Final fallback — stop-word strip
        if not product_keyword:
            product_keyword = extract_product_keyword(cleaned_query)
            product_method  = "stopword"

        logger.debug(f"[NLU] Step4 final product={product_keyword!r} via={product_method}")

        # ==================================================================
        # Build OS/ORM filters
        # ==================================================================
        os_filter = _build_perspective_filter(intent, ui_context, resolved_country)
        if price_filter:
            os_filter.setdefault("bool", {}).setdefault("must", []).append(price_filter)

        result = {
            "intent":          intent,
            "product":         product_keyword,
            "product_keyword": product_keyword,
            "country":         resolved_country,
            "quantity":        quantity,
            "price_filter":    price_filter,
            "os_filter":       os_filter,
            "entities":        entities,
            "ui_context":      ui_context,
        }

        logger.info(
            f"[NLU] Final parse | intent={intent} | product={product_keyword!r} | "
            f"country={resolved_country!r} | price={llm_result.get('price')} | "
            f"quantity={quantity!r} | product_method={product_method}"
        )
        t_total_nlu = (time.perf_counter() - t_nlu_total) * 1000
        logger.info(f"[LATENCY] NLU Total: {t_total_nlu:.0f}ms")
        logger.info(f"[LATENCY] NLU Total (no DeepSeek): {t_total_nlu - t_deepseek:.0f}ms")
        return result

    # Alias used by some views
    def get_search_filters(self, query: str, ui_context: str = "import") -> dict:
        return self.parse(query, ui_context=ui_context)

    # ------------------------------------------------------------------
    # Country Resolver (RapidFuzz)
    # ------------------------------------------------------------------
    
    def _resolve_country(self, raw_country: str) -> Optional[str]:
        """
        Uses RapidFuzz to map an extracted messy location ("chinaaa", "pak")
        to standard list.
        """
        # STOPWORDS block to catch meta-words BEFORE they reach RapidFuzz
        STOPWORDS = {
            "countries", "country", "international", "global", "worldwide", "abroad", 
            "all", "any", "some", "which", "what", "where", "who", "how", "the", "for"
        }
        if raw_country.lower().strip() in STOPWORDS:
            return None

        try:
            import rapidfuzz
        except ImportError:
            return raw_country.capitalize()
            
        STANDARD_COUNTRIES = [
            "Pakistan", "China", "United States", "India", "Afghanistan",
            "United Arab Emirates", "Saudi Arabia", "Germany", "United Kingdom",
            "Australia", "Canada", "Singapore", "Malaysia", "Indonesia",
            "Turkey", "Brazil", "France", "Italy", "Spain", "Japan", "South Korea",
            "Vietnam", "Thailand", "Egypt", "South Africa", "Nigeria", "Kenya"
        ]
        
        match = rapidfuzz.process.extractOne(
            raw_country.lower(), 
            STANDARD_COUNTRIES, 
            scorer=rapidfuzz.fuzz.WRatio, 
            score_cutoff=60.0 # Lowered slightly for "turk" -> "Turkey"
        )
        if match:
            return match[0] # The matched string (e.g., "China")
        return raw_country.capitalize() # fallback

    def _detect_country_fallback(self, query: str) -> Optional[str]:
        """
        Regex fallback to detect common countries if GLiNER misses them
        or if we want to bypass fuzzy matching for strict abbreviations (ira -> Iran).
        """
        q = query.lower()
        
        FALLBACK_COUNTRIES = {
            "china": "China", "chinaaa": "China", "chin": "China", "chi": "China",
            "pakistan": "Pakistan", "pak": "Pakistan", "pk": "Pakistan",
            "india": "India", "ind": "India",
            "turkey": "Turkey", "turk": "Turkey", "turkiye": "Turkey", "turekyy": "Turkey", "turky": "Turkey", "turke": "Turkey", "turkeyy": "Turkey",
            "usa": "United States", "us": "United States", "america": "United States",
            "uk": "United Kingdom", "britain": "United Kingdom", "england": "United Kingdom",
            "germany": "Germany", "france": "France", "italy": "Italy", "span": "Spain",
            "uae": "United Arab Emirates", "dubai": "United Arab Emirates",
            "saudi": "Saudi Arabia", "ksa": "Saudi Arabia",
            "iran": "Iran", "ira": "Iran",
            "egypt": "Egypt", "egyp": "Egypt",
            "korea": "South Korea", "kore": "South Korea", "south": "South Korea", "korean": "South Korea",
            "japan": "Japan", "jap": "Japan",
            "malaysia": "Malaysia", "malay": "Malaysia",
            "vietnam": "Vietnam", "viet": "Vietnam",
        }
        
        # Check explicit isolated words
        words = re.findall(r'\b\w+\b', q)
        for w in words:
            if w in FALLBACK_COUNTRIES:
                return FALLBACK_COUNTRIES[w]
                
        # Words that look geography-related but are NOT country names — never feed to RapidFuzz
        blacklisted_words = {
            "from", "for", "the", "and", "with", "in", "to",
            "buy", "sell", "get", "import", "export", "need", "want", "looking",
            # Geographic meta-words that confuse RapidFuzz
            "country", "countries", "international", "global", "worldwide", "abroad",
        }
        
        try:
            import rapidfuzz
            STANDARD_COUNTRIES = [
                "Pakistan", "China", "United States", "India", "Afghanistan",
                "United Arab Emirates", "Saudi Arabia", "Germany", "United Kingdom",
                "Australia", "Canada", "Singapore", "Malaysia", "Indonesia",
                "Turkey", "Brazil", "France", "Italy", "Spain", "Japan", "South Korea",
                "Vietnam", "Thailand", "Egypt", "South Africa", "Nigeria", "Kenya"
            ]
            for w in words:
                if len(w) >= 4 and w not in blacklisted_words:
                    match = rapidfuzz.process.extractOne(
                        w, STANDARD_COUNTRIES, scorer=rapidfuzz.fuzz.WRatio, score_cutoff=85.0
                    )
                    if match:
                        return match[0]
        except ImportError:
            pass
            
        return None



# ===========================================================================
# Diagnostic Verification
# ===========================================================================

def verify_nlu_performance():
    """
    Tests canonical trade scenarios.
    Run directly: python -m search.services.nlu_engine
    """
    test_queries = [
        ("i want to buy dextrose anhydrous", "import"),
        ("find buyers for basmati rice",     "import"),
        ("I WANT TO SELL fruc",              "import"),
        ("sugar under $500",                 "export"),
        ("dex",                              "import"),
        ("looking for buyers of urea 46%",   "import"),
    ]

    print("\n" + "=" * 65)
    print("  ZaraiLink NLU + Keyword Extraction Report")
    print("=" * 65)

    engine = ModernNLUEngine()

    for raw_query, ctx in test_queries:
        result = engine.parse(raw_query, ui_context=ctx)
        kw     = extract_product_keyword(raw_query)
        print(f"\n  Query   : {raw_query!r}")
        print(f"  Context : {ctx}")
        print(f"  Intent  : {result['intent']}")
        print(f"  Keyword : {kw!r}")
        print(f"  Product : {result['product']}")
        print(f"  Country : {result['country']}")
        print(f"  Price   : {result['price_filter']}")

    print("\n" + "=" * 65)
    print("  Done.")
    print("=" * 65)


if __name__ == "__main__":
    verify_nlu_performance()
