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
_SERVICE_DIR = Path(__file__).parent
_INTENT_MODEL_PATH = _SERVICE_DIR / ".." / "models" / "intent_model"

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
    
    # DIAGNOSTIC LOG FOR 401 ERRORS
    api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
    if api_key:
        logger.warning(f"[AuthCheck] API Key loaded. First 8 chars: '{api_key[:8]}', len: {len(api_key)}")
    else:
        logger.warning("[AuthCheck] API KEY IS EMPTY OR NONE!")
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 100,
        "response_format": {"type": "json_object"}
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=3)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        logger.warning(f"Primary LLM failed: {e}")
        # Fallback
        payload["model"] = "meta-llama/llama-3.3-70b-instruct"
        if "response_format" in payload:
            del payload["response_format"]
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=3)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            return json.loads(content)
        except Exception as fallback_e:
            logger.warning(f"Fallback LLM failed: {fallback_e}")
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


def _build_price_filter(raw_query: str) -> Optional[dict]:
    """
    Calls LLM via OpenRouter to extract price constraints and convert to OpenSearch range filter.
    Falls back to regex extraction if the LLM is unavailable or returns an error.
    Also returns ranking_hint for use by the ranking layer.
    """
    sys_prompt = '''You are a price constraint extractor for a trade search engine.
Return ONLY valid JSON, no markdown, no explanation:
{
  "operator": "lte" | "gte" | "range" | null,
  "value": <number or null>,
  "tolerance": <0.0-1.0 or null>,
  "is_ranking_signal_only": true | false,
  "ranking_hint": "price_asc" | "price_desc" | null
}
Rules:
- No price in query → all nulls
- cheap/affordable/budget with no number → is_ranking_signal_only: true, ranking_hint: "price_asc"
- around/roughly X → range operator, tolerance: 0.15
- Written numbers → integers (eight hundred → 800)
- Strip currency symbols
- under/below/less than/cheaper than/no more than → lte
- above/over/more than/at least → gte
- On any ambiguity return nulls, never guess'''

    try:
        parsed = _call_openrouter_llm(sys_prompt, raw_query)
        if not parsed:
            raise ValueError("LLM returned empty result")

        op_key            = parsed.get("operator")
        val               = parsed.get("value")
        ranking_hint      = parsed.get("ranking_hint")
        is_signal_only    = parsed.get("is_ranking_signal_only", False)

        logger.warning(f"[LLM-Price] Success: {parsed}")
        logger.warning(
            f"[LLM-Price] op={op_key!r} val={val!r} "
            f"ranking_hint={ranking_hint!r} signal_only={is_signal_only}"
        )

        # "cheap" with no number → ranking-only, no range filter
        if is_signal_only and not val:
            return {"ranking_hint": ranking_hint} if ranking_hint else None

        if op_key in ("lte", "gte") and val is not None:
            return {"range": {"usd_per_mt": {op_key: float(val)}}, "ranking_hint": ranking_hint}

        elif op_key == "range" and val is not None:
            tol = parsed.get("tolerance") or 0.15
            val = float(val)
            return {
                "range": {"usd_per_mt": {"gte": val * (1 - tol), "lte": val * (1 + tol)}},
                "ranking_hint": ranking_hint,
            }

        # LLM returned all nulls — try regex
        regex_result = _build_price_filter_regex(raw_query)
        if regex_result:
            logger.warning(f"[Price] LLM returned nulls; regex fallback yielded: {regex_result}")
        return regex_result

    except Exception as e:
        logger.warning(f"[LLM-Price] Failed: {e}")
        logger.warning(f"[LLM-Price] LLM unavailable ({e}); using regex fallback")
        return _build_price_filter_regex(raw_query)



def _extract_product_llm(raw_query: str) -> Optional[str]:
    sys_prompt = '''Extract only the product name from this trade search query.
Return ONLY a JSON object: {"product": <string or null>}
Ignore words like: supplier, cheap, bulk, buy, sell, from, china, quality, best, unga, bunga, etc.
Expand ALL abbreviations before returning:
  dex, dextros, dextrose -> dextrose
  gluc, glucos -> glucose
  citric, cit acid -> citric acid
  vitc, vit c, vitamin c -> vitamin c
  msg -> monosodium glutamate
  nh3 -> ammonia
  soda ash, soda -> soda ash
  naoh -> sodium hydroxide
  urea -> urea
  lac, lactos -> lactose
If no product can be identified return {"product": null}'''

    logger.info(f"[LLM-Product] Fallback triggered for query: {raw_query!r}")
    try:
        parsed = _call_openrouter_llm(sys_prompt, raw_query)
        logger.info(f"[LLM-Product] Raw LLM response: {parsed}")
        if parsed and parsed.get("product"):
            product = str(parsed["product"])
            logger.info(f"[LLM-Product] Resolved product: {product!r}")
            return product
        logger.info("[LLM-Product] LLM returned null product.")
        return None
    except Exception as e:
        logger.warning(f"[LLM-Product] Error in LLM product extraction: {e}")
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
    worldwide   | BUY    | PK user imports → find foreign suppliers
    worldwide   | SELL   | PK user exports → find foreign buyers
    pakistan    | BUY    | Foreigner buys FROM Pakistan (PK exports)
    pakistan    | SELL   | Foreigner sells TO Pakistan  (PK imports)
    ------------------------------------------------------------------
    """
    ctx = ui_context.lower()
    must: list[dict] = []

    if ctx == "worldwide":
        if intent == "BUY":
            must.append({"term": {"trade_type": {"value": "IMPORT", "case_insensitive": True}}})
        else:
            must.append({"term": {"trade_type": {"value": "EXPORT", "case_insensitive": True}}})
    elif ctx == "pakistan":
        if intent == "BUY":
            must.append({"term": {"trade_type": {"value": "EXPORT", "case_insensitive": True}}})
        else:
            must.append({"term": {"trade_type": {"value": "IMPORT", "case_insensitive": True}}})

    country_filters = []
    if ctx == "worldwide":
        if intent == "BUY" and country:
            country_filters.append({"term": {"origin_country": {"value": country, "case_insensitive": True}}})
        elif intent == "SELL" and country:
            country_filters.append({"term": {"destination_country": {"value": country, "case_insensitive": True}}})
    elif ctx == "pakistan":
        if intent == "BUY":
            country_filters.append({"term": {"origin_country": {"value": "Pakistan", "case_insensitive": True}}})
            if country:
                country_filters.append({"term": {"destination_country": {"value": country, "case_insensitive": True}}})
        else:
            country_filters.append({"term": {"destination_country": {"value": "Pakistan", "case_insensitive": True}}})
            if country:
                country_filters.append({"term": {"origin_country": {"value": country, "case_insensitive": True}}})

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
    Phase-3 NLU Engine with Hybrid NLP (GLiNER + RapidFuzz + Stopword Strip).
    Models are loaded lazily and cached as class attributes.
    Gracefully degrades to keyword-based intent + stop-word product extraction
    when ML models are unavailable.
    """

    _intent_model = None   # SetFit model
    _ner_model    = None   # GLiNER model

    GLINER_LABELS = [
        "product", "country", "quantity", "unit",
        "price", "currency", "price_operator",
    ]

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    @classmethod
    def _load_intent_model(cls):
        if cls._intent_model is not None:
            return

        model_path = str(_INTENT_MODEL_PATH.resolve())

        config_exists = os.path.exists(os.path.join(model_path, "config_setfit.json"))
        head_exists   = os.path.exists(os.path.join(model_path, "model_head.pkl"))

        if not (config_exists and head_exists):
            logger.info(
                f"SetFit model not found at {model_path}. "
                "Using keyword intent fallback."
            )
            return

        try:
            from setfit import SetFitModel
            logger.info(f"Loading SetFit intent model from {model_path}")
            cls._intent_model = SetFitModel.from_pretrained(model_path)
            logger.info("SetFit model loaded.")
        except Exception as e:
            logger.error(f"Failed to load SetFit model: {e}")

    @classmethod
    def _load_ner_model(cls):
        if cls._ner_model is not None:
            return
        try:
            from gliner import GLiNER
            logger.info("Loading GLiNER model: urchade/gliner_base ...")
            cls._ner_model = GLiNER.from_pretrained("urchade/gliner_base")
            logger.info("GLiNER loaded.")
        except Exception as e:
            logger.info(f"GLiNER not available — will use keyword product extraction: {e}")

    def __init__(self):
        self._load_intent_model()
        self._load_ner_model()

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------

    def predict_intent(self, query: str) -> str:
        """Returns 'BUY' or 'SELL'. 
        Prioritizes explicit keywords to prevent the model from mispredicting messy queries.
        """
        q = query.lower()
        
        # 1. Strong Regex Overrides
        # Handles extreme typos like "buyyyyy", "gettsds", "importtt"
        if re.search(r'\b(sell\w*|export\w*|supply\w*|distribute\w*|buyer\w*)\b', q):
            return "SELL"
            
        if re.search(r'\b(buy\w*|import\w*|get\w*|purchas\w*|need\w*|supplier\w*)\b', q):
            return "BUY"

        # 2. ML Model Fallback
        if self._intent_model is None:
            return "BUY"

        pred = self._intent_model.predict([query])[0]
        if isinstance(pred, str):
            return pred.upper()
        return "BUY" if int(pred) == 0 else "SELL"

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

    def parse(self, query: str, ui_context: str = "worldwide") -> dict:
        """
        Full NLU parse with perspective mapping.

        Returns:
            {
                "intent":          "BUY" | "SELL",
                "product":         str | None,    # GLiNER entity (may be None)
                "product_keyword": str,           # Stop-word stripped keyword (always set)
                "country":         str | None,
                "quantity":        str | None,
                "price_filter":    dict | None,
                "os_filter":       dict,
                "entities":        list[dict],
                "ui_context":      str,
            }
        """
        intent   = self.predict_intent(query)
        # ------------------------------------------------------------------
        # PASS 1: Entity Extraction (NER via GLiNER)
        # ------------------------------------------------------------------
        entities = self.extract_entities(query)
        
        extracted_product = _extract_entity(entities, "product")
        if not extracted_product:
            extracted_product = _extract_product_llm(query)
            
        extracted_country = _extract_entity(entities, "country") or _extract_entity(entities, "location")
        if not extracted_country:
            extracted_country = self._detect_country_fallback(query)
            
        quantity          = _extract_entity(entities, "quantity")
        price_filter      = _build_price_filter(query)

        # ------------------------------------------------------------------
        # PASS 2: Country Resolver (RapidFuzz / Regex Prep)
        # ------------------------------------------------------------------
        # First, see if we can find a hardcoded explicit match in the query (safest & fastest)
        resolved_country = self._detect_country_fallback(query)
        
        # If no hard match but GLiNER found a location entity, try to resolve it via RapidFuzz
        if not resolved_country and extracted_country:
            resolved_country = self._resolve_country(extracted_country)
            
        # ------------------------------------------------------------------
        # PASS 3: Product Matcher Prep (Cleanup)
        # ------------------------------------------------------------------
        # If we successfully resolved a country, strip it completely from the raw query
        # so it doesn't contaminate the product keyword (e.g. "dextrose from chinaaa" -> "dextrose")
        cleaned_query = query
        if extracted_country:
            # removing the raw extracted string
            cleaned_query = re.sub(r'\b' + re.escape(extracted_country) + r'\b', ' ', cleaned_query, flags=re.IGNORECASE)
            
        product_keyword = extract_product_keyword(cleaned_query)

        # Build final specific OS/ORM filters
        os_filter = _build_perspective_filter(intent, ui_context, resolved_country)

        if price_filter:
            if os_filter:
                os_filter.setdefault("bool", {}).setdefault("must", []).append(price_filter)
            else:
                os_filter = {"bool": {"must": [price_filter]}}



        return {
            "intent":          intent,
            "product":         extracted_product, # Uses LLM fallback if GLiNER fails
            "product_keyword": product_keyword,
            "country":         resolved_country,
            "quantity":        quantity,
            "price_filter":    price_filter,
            "os_filter":       os_filter,
            "entities":        entities,
            "ui_context":      ui_context,
        }

    # Alias used by some views
    def get_search_filters(self, query: str, ui_context: str = "worldwide") -> dict:
        return self.parse(query, ui_context=ui_context)

    # ------------------------------------------------------------------
    # Country Resolver (RapidFuzz)
    # ------------------------------------------------------------------
    
    def _resolve_country(self, raw_country: str) -> Optional[str]:
        """
        Uses RapidFuzz to map an extracted messy location ("chinaaa", "pak")
        to standard list.
        """
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
                
        # Fuzzy scan for missed countries, safely ignoring English stop words
        blacklisted_words = {"from", "for", "the", "and", "with", "in", "to", "buy", "sell", "get", "import", "export", "need", "want", "looking"}
        
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
        ("i want to buy dextrose anhydrous", "worldwide"),
        ("find buyers for basmati rice",     "worldwide"),
        ("I WANT TO SELL fruc",              "worldwide"),
        ("sugar under $500",                 "pakistan"),
        ("dex",                              "worldwide"),
        ("looking for buyers of urea 46%",   "worldwide"),
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
