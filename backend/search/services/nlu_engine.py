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

import pycountry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# pycountry-based country catalog (built once at module load)
# Keys: lowercase name, alpha-2, alpha-3, common_name, plus manual aliases.
# Values: the canonical country name string (e.g. "Brazil").
# ---------------------------------------------------------------------------

def _build_country_catalog() -> dict:
    catalog: dict = {}
    for c in pycountry.countries:
        catalog[c.name.lower()]        = c.name
        catalog[c.alpha_2.lower()]     = c.name
        catalog[c.alpha_3.lower()]     = c.name
        if hasattr(c, 'common_name'):
            catalog[c.common_name.lower()] = c.name
    # Manual aliases that pycountry misses or names differently
    _MANUAL: dict = {
        "pak":           "Pakistan",
        "uae":           "United Arab Emirates",
        "uk":            "United Kingdom",
        "usa":           "United States",
        "prc":           "China",
        "ksa":           "Saudi Arabia",
        "brasil":        "Brazil",
        "england":       "United Kingdom",
        "america":       "United States",
        "chn":           "China",
        "ger":           "Germany",
        "fra":           "France",
        "korea":         "South Korea",
        "s korea":       "South Korea",
        "south korea":   "South Korea",
        "n korea":       "North Korea",
        "north korea":   "North Korea",
        "korea republic": "South Korea",
    }
    catalog.update(_MANUAL)
    return catalog

_COUNTRY_CATALOG: dict = _build_country_catalog()
_COUNTRY_CATALOG_KEYS: list = list(_COUNTRY_CATALOG.keys())

# Fuzzy matching corpus — full names only (excludes alpha-2/alpha-3 codes).
# This prevents short typos like 'chna' from spuriously matching 'che' (Switzerland).
_COUNTRY_NAMES_ONLY: list = (
    [c.name.lower() for c in pycountry.countries]
    + [c.common_name.lower() for c in pycountry.countries if hasattr(c, 'common_name')]
)

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
# Ranking hint signals — ordered lists so multi-word phrases are checked FIRST
# to prevent ambiguous single words (e.g. "top") from matching too early.
# ---------------------------------------------------------------------------
# Each entry: (hint_value, [phrase, ...])  — phrases are case-insensitive substrings.
_RANKING_HINT_SIGNALS: list[tuple[str, list[str]]] = [
    # ── price_desc multi-word first (before bare "top" matches volume_desc) ──
    ("price_desc",  ["best quality", "top quality", "high value", "highest price", "premium quality"]),
    # ── reliability multi-word ────────────────────────────────────────────────
    ("reliability", ["serious buyers only", "serious sellers only", "verified only"]),
    # ── volume_desc multi-word ────────────────────────────────────────────────
    ("volume_desc", ["most active", "highest volume", "large quantities", "large scale",
                     "bulk buyers", "bulk sellers", "top importers", "top exporters",
                     "top suppliers", "top buyers", "biggest buyers", "biggest suppliers"]),
    # ── price_asc multi-word ─────────────────────────────────────────────────
    ("price_asc",   ["low price", "lowest price", "best price", "cheapest possible"]),
    # ── single-word signals (checked last) ───────────────────────────────────
    ("price_asc",   ["cheap", "cheapest", "affordable", "inexpensive", "budget"]),
    ("price_desc",  ["expensive", "premium"]),
    ("volume_desc", ["biggest", "largest", "leading", "major", "bulk", "top"]),
    ("reliability", ["reliable", "trusted", "established", "verified", "reputable", "serious"]),
]


def _detect_ranking_hint(raw_query: str) -> Optional[str]:
    """
    Scan the raw query for ranking preference signals and return the most
    specific match, or None if no signal is found.

    Priority: price_desc multi-word > reliability > volume_desc multi-word >
              price_asc multi-word > price_asc single > price_desc single >
              volume_desc single > reliability single

    Examples:
        "need cheap sugar"               → "price_asc"
        "premium dextrose from germany"  → "price_desc"
        "biggest buyers of sugar"        → "volume_desc"
        "serious buyers only"            → "reliability"
        "buy sugar from brazil"          → None
    """
    q = raw_query.lower()
    for hint, phrases in _RANKING_HINT_SIGNALS:
        for phrase in phrases:
            if phrase in q:
                return hint
    return None


# ---------------------------------------------------------------------------
# RapidFuzz noise token stripping
# Removes garbled trade verbs/adjectives that survive the stop-word regex.
# Examples: "molases exprt" → "molases",  "sugr cheep" → "sugr"
# Only strips tokens from MULTI-WORD keywords (single words are left alone).
# ---------------------------------------------------------------------------
_KNOWN_NOISE = [
    "export", "import", "buy", "sell", "cheap", "bulk",
    "urgent", "fast", "suppliers", "buyers", "from", "find",
    "need", "want", "get", "source", "looking", "supply",
    "purchase", "order", "enquiry", "inquiry", "quote",
]


def strip_noise_tokens(keyword: str) -> str:
    """
    Remove tokens that fuzzy-match known trade noise words (score >= 80).
    Only acts on multi-word keywords to avoid stripping real product names.

    Examples:
        'molases exprt'   → 'molases'
        'sugr cheep'      → 'sugr'
        'dextrose'        → 'dextrose'  (unchanged — single word)
    """
    tokens = keyword.split()
    if len(tokens) <= 1:
        return keyword   # Never strip a single-word product name
    try:
        from rapidfuzz import process, fuzz
        clean = []
        for token in tokens:
            match = process.extractOne(
                token, _KNOWN_NOISE,
                scorer=fuzz.WRatio,
                score_cutoff=80,
            )
            if not match:
                clean.append(token)
        result = " ".join(clean).strip()
        return result if result else keyword   # Safety: never return empty string
    except Exception:
        return keyword   # Graceful fallback if RapidFuzz unavailable


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
    # Prepositions — must be here so extract_product_keyword() strips them
    # when they survive after the country token is removed from cleaned_query.
    # e.g. "suggar from brazil" → country stripped → "suggar from " → "suggar"
    "from", "frm",
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

    # 1. Strip each stop phrase (longest first already, since list is ordered).
    # This must be done BEFORE the dynamic single-word verb stripping, 
    # otherwise phrases like "i wanna buy" get broken into "i     " and fail to match.
    for phrase in _INTENT_STOP_PHRASES:
        # Word-boundary aware replacement
        q = re.sub(r'\b' + re.escape(phrase) + r'\b', ' ', q)

    # 2. Dynamic Stripping of garbled intent verbs (buyyy, gettsds, importttt, etc.)
    # \w* catches ANY junk characters appended to the base word
    q = re.sub(r'\b(buy\w*|sell\w*|get\w*|import\w*|export\w*|purchas\w*|wanna|want\w*)\b', ' ', q)

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
        # Product spans — multiple labels improve recall across query styles
        "product", "commodity", "agricultural product", "trade good",
        # Trade context
        "country", "quantity", "unit",
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
            # torch 2.6+ + transformers 4.45+ default to meta-tensor init when
            # accelerate is installed, then crash on .to('cpu') with "Cannot
            # copy out of meta tensor". Two layers of defense:
            #   1. Pass low_cpu_mem_usage=False through SetFit's model_kwargs.
            #   2. Temporarily lie about accelerate availability so even
            #      sub-loads inside SetFit (e.g. its sentence-transformers
            #      body) skip the init_empty_weights path. Without (2) the
            #      first warmup attempt still races against accelerate state.
            import transformers.utils.import_utils as _tu
            _orig_is_accelerate = _tu.is_accelerate_available
            try:
                _tu.is_accelerate_available = lambda *a, **kw: False
                cls._intent_model = SetFitModel.from_pretrained(
                    model_path,
                    model_kwargs={"low_cpu_mem_usage": False},
                )
            finally:
                _tu.is_accelerate_available = _orig_is_accelerate
            logger.info("[NLU] SetFit model loaded successfully.")
        except Exception as e:
            logger.error(f"[NLU] Failed to load SetFit model: {e}. Using regex fallback.")

    @classmethod
    def _load_keyword_model(cls):
        """KeyBERT is intentionally disabled. Product extraction is handled by
        GLiNER (zero-shot, type-aware) followed by a regex fallback. KeyBERT
        produced untyped n-grams with informal-token noise (see context at
        line ~885) and was already unused in the live pipeline. _keyword_model
        stays None so any leftover read returns None gracefully."""
        return
        # ----- previous implementation kept for reference -----
        # if cls._keyword_model is not None:
        #     return
        # try:
        #     from keybert import KeyBERT
        #     logger.info("[NLU] Loading KeyBERT model ...")
        #     cls._keyword_model = KeyBERT(model="paraphrase-MiniLM-L6-v2")
        #     logger.info("[NLU] KeyBERT loaded.")
        # except Exception as e:
        #     logger.warning(f"[NLU] KeyBERT not available — will use stop-word extraction: {e}")

    @classmethod
    def _load_ner_model(cls):
        """Load GLiNER for entity extraction."""
        if cls._ner_model is not None:
            return
        try:
            from gliner import GLiNER
            logger.info("[NLU] Loading GLiNER model: urchade/gliner_base ...")
            # GLiNER's UniEncoderSpanModel does not accept model_kwargs, so we
            # cannot pass low_cpu_mem_usage=False the way we do for SetFit.
            # Instead, lie about accelerate availability for the duration of
            # the load — that forces transformers to skip its init_empty_weights
            # path entirely and materialize weights on CPU directly.
            import transformers.utils.import_utils as _tu
            _orig_is_accelerate = _tu.is_accelerate_available
            try:
                _tu.is_accelerate_available = lambda *a, **kw: False
                cls._ner_model = GLiNER.from_pretrained(
                    "urchade/gliner_base",
                    map_location="cpu",
                )
            finally:
                _tu.is_accelerate_available = _orig_is_accelerate
            logger.info("[NLU] GLiNER loaded.")
        except Exception as e:
            # Surface load failures at ERROR so they're visible in default Django
            # log config — silent INFO-level logging hid this for too long and
            # cascaded into "product=46" type bugs because the regex fallback
            # then mis-fires on short product names.
            logger.error(
                "[NLU] GLiNER failed to load — falling back to regex product "
                f"extraction. Error: {type(e).__name__}: {e}"
            )

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
        t_setfit = time.perf_counter() - t0

        # ==================================================================
        # STEP 1.5 — Pattern-Based Intent Override
        #
        # SetFit is accurate for most queries but misclassifies two specific
        # "who [seller-verb]s X" forms because it sees the verb alone and
        # ignores that the "who" subject means the user is FINDING that
        # counterparty, not being one.
        #
        # BUY overrides run FIRST so they cannot be overwritten by SELL overrides.
        # Placed AFTER SetFit so the model still runs (for telemetry) but
        # before any step that consumes `intent`.
        # ==================================================================
        _q_lower_intent = query.lower()

        # BUY overrides — "who [sells/exports/supplies]" = user wants to FIND sellers
        # SetFit sees the sell-verb and tags SELL; these patterns correct that.
        _BUY_OVERRIDE_PATTERNS = [
            r'\bwho\s+(?:sells?|sell)\b',                         # "who sells X"
            r'\bwho\s+(?:exports?|export)\b',                     # "who exports X"
            r'\bwho\s+(?:supplies?|supply)\b',                    # "who supplies X"
            r'\bwho\s+(?:is\s+)?(?:the\s+)?(?:exporter|seller|supplier)s?\b',  # "who is the exporter"
            r'\bwho\s+(?:are\s+)?(?:the\s+)?(?:exporters?|sellers?|suppliers?)\b',
        ]
        for _buy_pat in _BUY_OVERRIDE_PATTERNS:
            if re.search(_buy_pat, _q_lower_intent):
                logger.debug(f"[NLU] BUY override via pattern {_buy_pat!r} (was {intent!r})")
                intent = 'BUY'
                break
        else:
            # SELL overrides — only reached when no BUY pattern matched
            _SELL_OVERRIDE_PATTERNS = [
                r'\bwho\s+buys?\b',
                r'\bwho\s+(?:is\s+)?buying\b',
                r'\bwho\s+(?:are\s+)?(?:the\s+)?buyers?\b',
                r'\bwho\s+(?:is\s+)?(?:importing|imports?)\b',
                r'\blooking\s+to\s+(?:sell|export)\b',
                r'\bwant(?:ing)?\s+to\s+(?:sell|export)\b',
                r'\bwants?\s+to\s+(?:sell|export)\b',
                r'\bi\s+(?:want\s+to\s+)?(?:sell|export)\b',
            ]
            for _sell_pat in _SELL_OVERRIDE_PATTERNS:
                if re.search(_sell_pat, _q_lower_intent):
                    logger.debug(f"[NLU] SELL override via pattern {_sell_pat!r} (was {intent!r})")
                    intent = 'SELL'
                    break

        # ==================================================================
        # STEP 2 — GLiNER Entity Extraction
        # Runs once on the raw query. Extracts country (used in Step 3)
        # AND product spans (used in Step 4). Running on the raw query
        # (before country stripping) gives GLiNER full sentence context,
        # which improves span boundary detection.
        # ==================================================================
        t0 = time.perf_counter()
        entities = self.extract_entities(query)
        gliner_country = (
            _extract_entity(entities, "country")
            or _extract_entity(entities, "location")
        )
        t_gliner = time.perf_counter() - t0

        # ==================================================================
        # STEP 3 — Country Resolution
        # Layer 1: GLiNER (primary)
        # Layer 2: RapidFuzz preposition capture (fallback)
        # Layer 3: Abbreviations (last resort)
        # ==================================================================
        t0 = time.perf_counter()
        resolved_country = None
        if gliner_country:
            resolved_country = self._resolve_country(gliner_country)
        
        if not resolved_country:
            resolved_country = self._detect_country_fallback(query)
        t_rapidfuzz = time.perf_counter() - t0

        # ==================================================================
        # STEP 3.5 — Country Role Post-Processing
        #
        # Problem: the country extracted from "from [country]" in a SELL query
        # is the USER'S OWN origin, not a buyer/counterparty filter.
        # Applying it as a counterparty filter produces zero results because
        # the aggregator looks for buyers in that country, but the user's own
        # origin has nothing to do with where their buyers are.
        #
        # Examples of the problem:
        #   "who buys sugar from pakistan"      → Pakistan = Pakistan's own origin
        #   "looking to export dextrose from china" → China = supplier origin,
        #                                              not a buyer country
        #
        # Rule: if intent=SELL AND the resolved country appears after the
        # preposition "from" in the raw query → reclassify it as origin_country
        # (stored in the NLU result for informational use) and clear the DB filter.
        #
        # "in [country]" with SELL is intentionally kept as a filter, because
        # "who buys dextrose in Pakistan" legitimately means filter by
        # Pakistani buyers.
        # ==================================================================
        origin_country = None  # user's own country; never used as DB filter
        if intent == 'SELL' and resolved_country:
            _from_role_pat = re.compile(
                r'\bfrom\s+' + re.escape(resolved_country.lower()) + r'\b',
                re.IGNORECASE,
            )
            if _from_role_pat.search(query):
                origin_country   = resolved_country
                resolved_country = None
                logger.debug(
                    f"[NLU] Country role: {origin_country!r} reclassified as "
                    f"origin_country (SELL+from), cleared from DB filter."
                )

        # ==================================================================
        # STEP 4 — Product Keyword Extraction (GLiNER primary)
        #
        # GLiNER already ran on the raw query in Step 2 — we reuse those
        # entities here. No second model call needed.
        #
        # Why GLiNER instead of KeyBERT:
        #   KeyBERT uses CountVectorizer n-gram scoring. It sees "wanna sugar"
        #   as a high-scoring bigram because "wanna" is not a standard English
        #   stop-word and CountVectorizer generates bigrams before filtering.
        #   GLiNER does zero-shot span extraction using the full sentence
        #   context, so it correctly isolates "sugar" from
        #   "i wanna buy sugar from brazil".
        #
        # Priority: GLiNER span → extract_product_keyword() regex fallback
        # KeyBERT (_keyword_model) is intentionally not used for product
        # extraction but remains loaded for potential future use.
        # ==================================================================
        cleaned_query = query
        if resolved_country:
            cleaned_query = re.sub(
                r'\b' + re.escape(resolved_country) + r'\b', ' ',
                cleaned_query, flags=re.IGNORECASE,
            )
        # Also strip the raw misspelled token that resolved to the country
        # e.g. 'brzail' → Brazil: the re.sub above won't catch 'brzail'
        _prep_country_match = re.search(
            r'\b(?:from|frm|fron|form|in|based\s+in|located\s+in|within)\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
            cleaned_query.lower()
        )
        if _prep_country_match:
            _raw_token = _prep_country_match.group(1).strip()
            if _raw_token.lower() != (resolved_country or '').lower():
                cleaned_query = re.sub(
                    r'\b' + re.escape(_raw_token) + r'\b', ' ',
                    cleaned_query, flags=re.IGNORECASE,
                )

        product_keyword = None
        product_method  = "none"
        keybert_confidence = 0.0  # kept for telemetry schema compatibility

        t0 = time.perf_counter()

        # --- GLiNER product extraction (entities already computed in Step 2) ---
        gliner_product = (
            _extract_entity(entities, "product")
            or _extract_entity(entities, "commodity")
            or _extract_entity(entities, "agricultural product")
            or _extract_entity(entities, "trade good")
        )
        if gliner_product:
            raw_product = gliner_product.strip().lower()
            # Safety net: Reject GLiNER extraction if it's literally an action verb,
            # or if it starts with one (e.g. "export dextrose"), because the 
            # fallback extract_product_keyword() handles stripping these perfectly.
            _action_verbs = ("import", "export", "buy", "sell", "buying", "selling", "importing", "exporting")
            
            if raw_product in _action_verbs or raw_product.startswith(tuple(f"{v} " for v in _action_verbs)):
                logger.debug(f"[NLU] Rejected GLiNER product span {raw_product!r} (contains action verb)")
                product_keyword = None
            else:
                # Cross-check: only reject GLiNER's product span if it is *very*
                # close to a country name, AND the span itself is long enough that
                # a high fuzz score is meaningful (short tokens like 'urea' fuzzy-
                # match 'Korea' at ~67 — cutoff was 60, falsely deleting urea).
                _country_check = (
                    self._resolve_country(raw_product, cutoff=85.0)
                    if len(raw_product.replace(" ", "")) >= 6
                    else None
                )
                if _country_check:
                    logger.debug(f"[NLU] Rejected GLiNER product span {raw_product!r} — resolves as country {_country_check!r}")
                    product_keyword = None
                else:
                    product_keyword = raw_product
                    product_method  = "gliner"
                    logger.debug(f"[NLU] GLiNER product span: {product_keyword!r}")

        # Pure-Python post-processing on already-extracted GLiNER entities
        # (action-verb guard, country cross-check, label fallback chain).
        # No model inference happens here — the GLiNER forward pass already
        # ran in Step 2 (timed as t_gliner). Typically <1 ms.
        t_pick_product = time.perf_counter() - t0

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
        
        if not needs_llm:
            import copy
            llm_result  = copy.deepcopy(_LLM_UNIFIED_EMPTY)
            price_filter = regex_price # Use the fully built regex price filter
        else:
            llm_result = _call_llm_unified(query)
            price_filter = _price_filter_from_llm(llm_result)

        quantity     = llm_result.get("quantity")
        llm_product  = llm_result.get("product")

        # If KeyBERT returned nothing, use the LLM product
        if not product_keyword and llm_product:
            product_keyword = llm_product
            product_method  = "llm"

        # Final fallback — stop-word strip
        if not product_keyword:
            product_keyword = extract_product_keyword(cleaned_query)
            product_method  = "stopword"

        # ------------------------------------------------------------------
        # POST-EXTRACTION PREPOSITION RESIDUAL CLEANUP
        #
        # After the country token is stripped from cleaned_query, preposition
        # words like "from", "in", "frm" can survive if they happened to sit
        # between the product word and the country:
        #   "suggar from brazil" → Brazil stripped → "suggar from "
        #   → extract_product_keyword strips "from" (now in stop phrases)
        #   → "suggar"  ✓
        #
        # This second pass is a safety net for cases where the keyword was
        # already set by GLiNER or LLM and still contains a residual preposition
        # (e.g. GLiNER extracted "suggar from" as the product span).
        # ------------------------------------------------------------------
        if product_keyword:
            _PREP_RESIDUAL_RE = re.compile(
                r'\b(from|frm|fron|form|in|at|within|based|located|can|get|find|show|suppliers?|of)\b',
                re.IGNORECASE,
            )
            _cleaned_kw = _PREP_RESIDUAL_RE.sub(' ', product_keyword)
            _cleaned_kw = re.sub(r'\s+', ' ', _cleaned_kw).strip()
            if _cleaned_kw and _cleaned_kw != product_keyword:
                logger.debug(
                    f"[NLU] Preposition residual stripped from product_keyword: "
                    f"{product_keyword!r} → {_cleaned_kw!r}"
                )
                product_keyword = _cleaned_kw

        # ------------------------------------------------------------------
        # STEP 5.5 — Noise token stripping (garbled trade verbs/adjectives)
        # Runs after all extraction so we don't interfere with GLiNER/LLM.
        # Only strips multi-word keywords; single-word typos (e.g. 'sugr') are
        # left for the product resolver's PASS 4/5 to handle.
        # ------------------------------------------------------------------
        if product_keyword:
            _stripped = strip_noise_tokens(product_keyword)
            if _stripped != product_keyword:
                logger.debug(
                    f"[NLU] Noise strip: {product_keyword!r} → {_stripped!r}"
                )
                product_keyword = _stripped

        # Strip any residual country-like tokens from multi-word product keywords.
        # Cutoff raised from 65 → 88 to fix the urea→Korea / iron→Iran false-
        # positive class. Short, well-known country names ('china', 'uae',
        # 'japan') still resolve via the direct catalog lookup inside
        # _resolve_country (which ignores cutoff), so the higher cutoff only
        # blocks weak fuzzy matches against unrelated short product words.
        if product_keyword and len(product_keyword.split()) > 1:
            _kw_words = product_keyword.split()
            _kw_cleaned = [
                w for w in _kw_words
                if not self._resolve_country(w, cutoff=88.0)
            ]
            if _kw_cleaned and _kw_cleaned != _kw_words:
                product_keyword = ' '.join(_kw_cleaned).strip()
                logger.debug(f"[NLU] Country token removed from product: {_kw_words} → {product_keyword!r}")

        # Spell correct each word in multi-word product keywords
        if product_keyword and len(product_keyword.split()) > 1:
            try:
                from rapidfuzz import process, fuzz
                if hasattr(self, '_product_catalog_cache'):
                    _words = product_keyword.split()
                    _corrected_words = []
                    for _w in _words:
                        _m = process.extractOne(_w, self._product_catalog_cache, scorer=fuzz.ratio, score_cutoff=60)
                        _corrected_words.append(_m[0] if _m else _w)
                    product_keyword = ' '.join(_corrected_words).strip()
            except Exception:
                pass

        # ------------------------------------------------------------------
        # STEP 5.6 — RapidFuzz spell correction against product catalog
        # Only runs on single-word keywords (multi-word already cleaned above).
        # Corrects typos like 'sugr' → 'Sugar', 'dextrse' → 'Dextrose'.
        # Uses an instance-level cache so the DB query happens only once
        # per Django worker process lifetime.
        # ------------------------------------------------------------------
        if product_keyword and len(product_keyword.split()) == 1:
            try:
                from rapidfuzz import process, fuzz
                if not hasattr(self, '_product_catalog_cache'):
                    from trade_data.models import ProductSubCategory, ProductItem
                    _names = list(ProductSubCategory.objects.values_list('name', flat=True))
                    _names += list(ProductItem.objects.values_list('name', flat=True))
                    self._product_catalog_cache = list(set(n for n in _names if n))
                    logger.info(f"[NLU] SpellCorrect catalog loaded: {len(self._product_catalog_cache)} entries")

                _sc_match = process.extractOne(
                    product_keyword,
                    self._product_catalog_cache,
                    scorer=fuzz.ratio,
                    score_cutoff=60,
                )
                if _sc_match:
                    _corrected = _sc_match[0]
                    if _corrected.lower() != product_keyword.lower():
                        logger.debug(
                            f"[NLU] SpellCorrect: {product_keyword!r} → {_corrected!r} "
                            f"(score={_sc_match[1]:.1f})"
                        )
                        product_keyword = _corrected
            except Exception as _sc_err:
                logger.warning(f"[NLU] SpellCorrect failed: {_sc_err}")

        # ==================================================================
        # Build OS/ORM filters
        # ==================================================================
        os_filter = _build_perspective_filter(intent, ui_context, resolved_country)
        if price_filter:
            os_filter.setdefault("bool", {}).setdefault("must", []).append(price_filter)

        # ==================================================================
        # STEP 6 — Ranking Hint Detection
        # Runs on the raw query (before any stripping) to catch all signals.
        # The hint from price_filter (LLM/regex) is kept as a secondary source;
        # the direct scan here is the primary source for non-price signals.
        # ==================================================================
        ranking_hint = _detect_ranking_hint(query)
        # Merge: if price_filter already carries a hint (e.g. from LLM), prefer
        # the explicit price_filter hint for price signals only, otherwise use ours.
        price_filter_hint = (price_filter or {}).get("ranking_hint")
        if price_filter_hint and not ranking_hint:
            ranking_hint = price_filter_hint

        result = {
            "intent":          intent,
            "product":         product_keyword,
            "product_keyword": product_keyword,
            "country":         resolved_country,   # counterparty country for DB filter
            "origin_country":  origin_country,      # user's own origin (SELL queries); no DB filter
            "quantity":        quantity,
            "price_filter":    price_filter,
            "ranking_hint":    ranking_hint,        # top-level signal for _orm_search
            "os_filter":       os_filter,
            "entities":        entities,
            "ui_context":      ui_context,
            "timings": {
                "setfit": t_setfit,
                "gliner": t_gliner,                 # GLiNER forward pass (the only model call)
                "rapidfuzz": t_rapidfuzz,
                "pick_product": t_pick_product,     # post-processing on entities[]; no model run
                "total": time.perf_counter() - t_nlu_total,
            }
        }

        return result

    # Alias used by some views
    def get_search_filters(self, query: str, ui_context: str = "import") -> dict:
        return self.parse(query, ui_context=ui_context)

    # ------------------------------------------------------------------
    # Country Resolver (RapidFuzz)
    # ------------------------------------------------------------------
    
    def _resolve_country(self, raw_country: str, cutoff: float = 75.0) -> Optional[str]:
        """
        Uses RapidFuzz to map an extracted messy location ("chinaaa", "pak")
        to standard list.
        """
        # STOPWORDS block to catch meta-words BEFORE they reach RapidFuzz
        STOPWORDS = {
            "countries", "country", "international", "global", "worldwide", "abroad",
            "all", "any", "some", "which", "what", "where", "who", "how", "the", "for",
            "can", "get", "want", "wanna", "need", "please", "pls", "yo", "me", "us",
            "find", "show", "give", "tell", "help", "let", "make", "do", "go",
            "in", "to", "no",
        }
        if raw_country.lower().strip() in STOPWORDS:
            return None

        # Direct catalog lookup first (exact key hit — handles abbreviations like 'pak', 'uae')
        _direct = _COUNTRY_CATALOG.get(raw_country.lower().strip())
        if _direct:
            return _direct

        try:
            import rapidfuzz
        except ImportError:
            return None

        match = rapidfuzz.process.extractOne(
            raw_country.lower(),
            _COUNTRY_NAMES_ONLY,
            scorer=rapidfuzz.fuzz.WRatio,
            processor=rapidfuzz.utils.default_process,
            score_cutoff=cutoff,
        )
        if match:
            matched_key = match[0]
            return _COUNTRY_CATALOG.get(matched_key.lower())
        return None

    def _detect_country_fallback(self, query: str) -> Optional[str]:
        """
        Regex fallback to detect common countries if GLiNER misses them
        or if we want to bypass fuzzy matching for strict abbreviations (ira -> Iran).
        """
        q = query.lower()

        # ------------------------------------------------------------------
        # PREPOSITION-ANCHORED PASS
        # Match "from X", "in X", "based in X", "located in X", "within X"
        # and validate the captured text through _resolve_country (RapidFuzz).
        # Multi-word prepositions must come before single-word ones so that
        # "based in brazil" matches the longer pattern first.
        # False-positive guard: _resolve_country uses score_cutoff=60, so
        # non-country words like "food", "industry", "market" won't match.
        # ------------------------------------------------------------------
        _PREP_PATTERNS = [
            r'\b(?:based\s+in|located\s+in)\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
            r'\bwithin\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
            r'\b(?:from|frm|fron|form|in)\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
        ]
        _PREP_STANDARD_COUNTRIES = {
            "pakistan", "china", "united states", "india", "afghanistan",
            "united arab emirates", "saudi arabia", "germany", "united kingdom",
            "australia", "canada", "singapore", "malaysia", "indonesia",
            "turkey", "brazil", "france", "italy", "spain", "japan", "south korea",
            "vietnam", "thailand", "egypt", "south africa", "nigeria", "kenya",
        }
        _FORBIDDEN_PREFIXES = (
            # Question words
            "where", "who", "what", "which", "how",
            # Uncertainty
            "anywhere", "somewhere", "wherever", "any country", "anyplace", "any",
            # Hedge words
            "maybe", "perhaps", "possibly", "idk", "not sure"
        )

        has_preposition = re.search(r'\b(?:from|frm|fron|form|in|based\s+in|located\s+in|within)\b', q)

        for pattern in _PREP_PATTERNS:
            m = re.search(pattern, q)
            if m:
                candidate = m.group(1).strip()

                if candidate.startswith(_FORBIDDEN_PREFIXES):
                    continue

                # Direct catalog hit (handles 'pak', 'usa', exact country names)
                _direct = _COUNTRY_CATALOG.get(candidate.lower())
                if _direct:
                    return _direct

                # RapidFuzz fuzzy match at 65 threshold for preposition-anchored candidates
                resolved = self._resolve_country(candidate, cutoff=65.0)
                if resolved:
                    return resolved
                return None

        # ------------------------------------------------------------------
        # LAYER 3 — Free token scan using catalog (replaces hardcoded ABBREVIATIONS)
        # Checks every word in the query for a direct catalog hit first,
        # then RapidFuzz at 85 threshold for typo tolerance.
        # Skipped entirely when the query contains a preposition — the
        # anchored pass above already had the best opportunity to resolve
        # the country, and falling through here causes false positives
        # (e.g. 'brzail' → 'Anguilla' via a spurious short-key match).
        # ------------------------------------------------------------------
        if has_preposition:
            return None
        words = re.findall(r'\b\w+\b', q)
        for w in words:
            if len(w) < 4:
                continue
            direct = _COUNTRY_CATALOG.get(w)
            if direct:
                return direct

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
