from __future__ import annotations

import contextlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import pycountry

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _disable_meta_tensor_init():
    """Force transformers/accelerate to materialize weights on CPU directly.

    Why: torch >= 2.4 + transformers >= 4.45 default to a meta-tensor init
    path (`init_empty_weights()` then `_load_state_dict_into_meta_model`).
    For SetFit and GLiNER sub-loads this races with sentence-transformers'
    subsequent `.to('cpu')`, raising "Cannot copy out of meta tensor".

    How: rebind `is_accelerate_available` on the *call sites* that actually
    use it (transformers.modeling_utils caches the import at module load,
    so patching transformers.utils.import_utils alone is not enough), and
    swap `accelerate.init_empty_weights` for a no-op context manager so any
    code path that still goes through it just builds real CPU tensors.
    """
    patches: list[tuple[object, str, object]] = []

    def _patch(module, attr, value):
        if hasattr(module, attr):
            patches.append((module, attr, getattr(module, attr)))
            setattr(module, attr, value)

    try:
        import transformers.modeling_utils as _mu
        _patch(_mu, "is_accelerate_available", lambda *a, **k: False)
    except Exception:
        pass
    try:
        import transformers.utils.import_utils as _tu
        _patch(_tu, "is_accelerate_available", lambda *a, **k: False)
    except Exception:
        pass

    @contextlib.contextmanager
    def _noop_init_empty_weights(*args, **kwargs):
        yield

    try:
        import accelerate
        _patch(accelerate, "init_empty_weights", _noop_init_empty_weights)
        try:
            import accelerate.big_modeling as _bm
            _patch(_bm, "init_empty_weights", _noop_init_empty_weights)
        except Exception:
            pass
        try:
            import transformers.modeling_utils as _mu
            _patch(_mu, "init_empty_weights", _noop_init_empty_weights)
        except Exception:
            pass
    except Exception:
        pass

    try:
        yield
    finally:
        for module, attr, original in patches:
            setattr(module, attr, original)

# Country catalog: lowercase name/alpha-2/alpha-3/common_name + manual aliases
# -> canonical country name. Built once at module load.

def _build_country_catalog() -> dict:
    catalog: dict = {}
    for c in pycountry.countries:
        catalog[c.name.lower()]        = c.name
        catalog[c.alpha_2.lower()]     = c.name
        catalog[c.alpha_3.lower()]     = c.name
        if hasattr(c, 'common_name'):
            catalog[c.common_name.lower()] = c.name
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

# Fuzzy matching corpus is full names only — excluding alpha-2/3 codes prevents
# short typos like 'chna' from spuriously matching 'che' (Switzerland).
_COUNTRY_NAMES_ONLY: list = (
    [c.name.lower() for c in pycountry.countries]
    + [c.common_name.lower() for c in pycountry.countries if hasattr(c, 'common_name')]
)

_BACKEND_DIR       = Path(__file__).resolve().parent.parent.parent
_INTENT_MODEL_PATH = _BACKEND_DIR / "models" / "zarai_intent_model"

_LTE_PHRASES = {"under", "below", "max", "less than", "cheaper than", "at most"}
_GTE_PHRASES = {"above", "over", "min", "more than", "at least", "minimum"}

# Ranking-hint phrases — multi-word phrases come FIRST so ambiguous single words
# (e.g. "top") don't match before more specific phrases.
_RANKING_HINT_SIGNALS: list[tuple[str, list[str]]] = [
    ("price_desc",  ["best quality", "top quality", "high value", "highest price", "premium quality"]),
    ("reliability", ["serious buyers only", "serious sellers only", "verified only"]),
    ("volume_desc", ["most active", "highest volume", "large quantities", "large scale",
                     "bulk buyers", "bulk sellers", "top importers", "top exporters",
                     "top suppliers", "top buyers", "biggest buyers", "biggest suppliers"]),
    ("price_asc",   ["low price", "lowest price", "best price", "cheapest possible"]),
    ("price_asc",   ["cheap", "cheapest", "affordable", "inexpensive", "budget"]),
    ("price_desc",  ["expensive", "premium"]),
    ("volume_desc", ["biggest", "largest", "leading", "major", "bulk", "top"]),
    ("reliability", ["reliable", "trusted", "established", "verified", "reputable", "serious"]),
]


def _detect_ranking_hint(raw_query: str) -> Optional[str]:
    q = raw_query.lower()
    for hint, phrases in _RANKING_HINT_SIGNALS:
        for phrase in phrases:
            if phrase in q:
                return hint
    return None


# Garbled trade verbs that survive the stop-word regex (e.g. "exprt", "cheep").
# Only stripped from multi-word keywords.
_KNOWN_NOISE = [
    "export", "import", "buy", "sell", "cheap", "bulk",
    "urgent", "fast", "suppliers", "buyers", "from", "find",
    "need", "want", "get", "source", "looking", "supply",
    "purchase", "order", "enquiry", "inquiry", "quote",
]


def strip_noise_tokens(keyword: str) -> str:
    tokens = keyword.split()
    if len(tokens) <= 1:
        return keyword
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
        return result if result else keyword
    except Exception:
        return keyword


# Stop phrases stripped from the raw query before product name search.
# Order matters: multi-word phrases must come before single words.
_INTENT_STOP_PHRASES = [
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
    "where", "how", "what", "which",
    "buy", "sell", "purchase", "import", "export", "get",
    "supplier", "suppliers", "buyer", "buyers",
    "find", "search", "looking", "please", "need",
    # Prepositions: must be stripped here because they survive after the country
    # token is removed (e.g. "suggar from brazil" -> "suggar from " -> "suggar").
    "from", "frm",
    "for", "me", "best",
]


def extract_product_keyword(raw_query: str) -> str:
    q = raw_query.lower().strip()

    # Stop-phrase pass must run BEFORE dynamic verb stripping, otherwise phrases
    # like "i wanna buy" get split into "i     " and fail to match.
    for phrase in _INTENT_STOP_PHRASES:
        q = re.sub(r'\b' + re.escape(phrase) + r'\b', ' ', q)

    # \w* catches junk suffixes on intent verbs (buyyy, importttt, etc.)
    q = re.sub(r'\b(buy\w*|sell\w*|get\w*|import\w*|export\w*|purchas\w*|wanna|want\w*)\b', ' ', q)

    q = re.sub(r'\b(under|below|above|over|min|max|less than|more than|at most|at least)\s*\$?\d+(\s*(usd|pkr|per\s+mt))?\b', '', q)
    q = re.sub(r'\$\d+(\.\d+)?', '', q)

    q = re.sub(r'[^\w\s]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()

    words = q.split()
    if len(words) > 4:
        # Score candidates against the product catalog (TrigramSimilarity) instead
        # of picking the longest word. Length-only picked "unga" over "dex" in
        # "unga bunga dex".
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
                q = max(filtered, key=len)

    return q or raw_query.lower().strip()


def _detect_price_operator(query: str) -> Optional[str]:
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
        "model": "google/gemini-2.5-flash-lite",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }

    def _post_and_parse(p):
        resp = requests.post(url, headers=headers, json=p, timeout=8)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Gemini via OpenRouter sometimes ignores response_format and wraps JSON
        # in ```json fences — strip defensively.
        if content.startswith("```json"):
            content = content[7:].rsplit("```", 1)[0].strip()
        elif content.startswith("```"):
            content = content[3:].rsplit("```", 1)[0].strip()
        return json.loads(content)

    try:
        return _post_and_parse(payload)
    except Exception as e:
        logger.warning(f"[LLM] Primary model failed: {e}")
        # Retry without response_format in case the provider rejected it.
        retry = dict(payload)
        retry.pop("response_format", None)
        try:
            return _post_and_parse(retry)
        except Exception as retry_e:
            logger.warning(f"[LLM] Retry without response_format also failed: {retry_e}")
            return None

def _build_price_filter_regex(raw_query: str) -> Optional[dict]:
    q = raw_query.lower()

    price_ranking_words = {"cheap", "affordable", "budget", "cheapest", "low price", "best price", "inexpensive"}
    has_number = bool(re.search(r'\d', q))
    if not has_number and any(w in q for w in price_ranking_words):
        logger.warning("[RegexPrice] No-number price signal → ranking_hint=price_asc only")
        return {"ranking_hint": "price_asc"}

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
    # Returns _LLM_UNIFIED_EMPTY on any failure — never raises.
    import copy
    try:
        parsed = _call_openrouter_llm(_LLM_UNIFIED_PROMPT, raw_query)
        if not parsed:
            raise ValueError("LLM returned empty result")

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
    price = llm_result.get("price") or {}
    op    = price.get("operator")
    val   = price.get("value")
    hint  = price.get("ranking_hint")

    if op in ("lte", "gte") and val is not None:
        return {"range": {"usd_per_mt": {op: float(val)}}, "ranking_hint": hint}

    if hint:
        return {"ranking_hint": hint}

    return None


def _extract_entity(entities: list[dict], label: str) -> Optional[str]:
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
    Perspective table:
      import + BUY  -> Foreign Suppliers
      import + SELL -> Pakistani Buyers
      export + BUY  -> Pakistani Suppliers
      export + SELL -> Foreign Buyers
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


class ModernNLUEngine:
    _intent_model  = None
    _keyword_model = None
    _ner_model     = None

    GLINER_LABELS = [
        # Multiple product labels improve recall across query styles.
        "product", "commodity", "agricultural product", "trade good",
        "country", "quantity", "unit",
        "price", "currency", "price_operator",
    ]

    @classmethod
    def _load_intent_model(cls):
        if cls._intent_model is not None:
            return

        model_path = str(_INTENT_MODEL_PATH.resolve())

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
            with _disable_meta_tensor_init():
                cls._intent_model = SetFitModel.from_pretrained(
                    model_path,
                    model_kwargs={"low_cpu_mem_usage": False},
                )
            logger.info("[NLU] SetFit model loaded successfully.")
        except Exception as e:
            logger.error(f"[NLU] Failed to load SetFit model: {e}. Using regex fallback.")

    @classmethod
    def _load_keyword_model(cls):
        """KeyBERT is intentionally disabled — produced untyped n-grams with informal-token
        noise. GLiNER (zero-shot, type-aware) + regex fallback handle product extraction.
        _keyword_model stays None so leftover reads return None gracefully."""
        return
        # Previous implementation kept for reference:
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
        if cls._ner_model is not None:
            return
        try:
            from gliner import GLiNER
            logger.info("[NLU] Loading GLiNER model: urchade/gliner_base ...")
            with _disable_meta_tensor_init():
                cls._ner_model = GLiNER.from_pretrained(
                    "urchade/gliner_base",
                    map_location="cpu",
                )
            logger.info("[NLU] GLiNER loaded.")
        except Exception as e:
            # Log at ERROR so default Django log config surfaces it — silent INFO
            # hid this and cascaded into "product=46" bugs via the regex fallback.
            logger.error(
                "[NLU] GLiNER failed to load — falling back to regex product "
                f"extraction. Error: {type(e).__name__}: {e}"
            )

    def __init__(self):
        self._load_intent_model()
        self._load_keyword_model()
        self._load_ner_model()

    def predict_intent(self, query: str) -> str:
        if self._intent_model is not None:
            try:
                pred = self._intent_model.predict([query])[0]
                if isinstance(pred, str):
                    return pred.upper()
                return "BUY" if int(pred) == 0 else "SELL"
            except Exception as e:
                logger.warning(f"[NLU] SetFit inference failed: {e}. Using regex fallback.")

        q = query.lower()
        if re.search(r'\b(sell\w*|export\w*|supply\w*|distribute\w*|buyer\w*)\b', q):
            return "SELL"
        if re.search(r'\b(buy\w*|import\w*|get\w*|purchas\w*|need\w*|supplier\w*)\b', q):
            return "BUY"

        return "UNKNOWN"

    def extract_entities(self, query: str) -> list[dict]:
        if self._ner_model is None:
            return []
        try:
            return self._ner_model.predict_entities(
                query, labels=self.GLINER_LABELS, threshold=0.3
            )
        except Exception as e:
            logger.error(f"GLiNER inference error: {e}")
            return []

    def parse(self, query: str, ui_context: str = "import") -> dict:
        import time
        t_nlu_total = time.perf_counter()

        t0 = time.perf_counter()
        intent = self.predict_intent(query)
        t_setfit = time.perf_counter() - t0

        # SetFit misclassifies "who [sells/exports]" — the verb tags SELL but the
        # "who" subject means the user wants to FIND sellers, not be one.
        # BUY overrides run first so SELL overrides can't overwrite them.
        _q_lower_intent = query.lower()

        _BUY_OVERRIDE_PATTERNS = [
            r'\bwho\s+(?:sells?|sell)\b',
            r'\bwho\s+(?:exports?|export)\b',
            r'\bwho\s+(?:supplies?|supply)\b',
            r'\bwho\s+(?:is\s+)?(?:the\s+)?(?:exporter|seller|supplier)s?\b',
            r'\bwho\s+(?:are\s+)?(?:the\s+)?(?:exporters?|sellers?|suppliers?)\b',
        ]
        for _buy_pat in _BUY_OVERRIDE_PATTERNS:
            if re.search(_buy_pat, _q_lower_intent):
                logger.debug(f"[NLU] BUY override via pattern {_buy_pat!r} (was {intent!r})")
                intent = 'BUY'
                break
        else:
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

        # Run GLiNER on the raw query (pre-country-strip) so it has full sentence
        # context for span detection. Country and product spans both extracted here.
        t0 = time.perf_counter()
        entities = self.extract_entities(query)
        gliner_country = (
            _extract_entity(entities, "country")
            or _extract_entity(entities, "location")
        )
        t_gliner = time.perf_counter() - t0

        # Country: GLiNER -> RapidFuzz preposition capture -> abbreviation scan.
        t0 = time.perf_counter()
        resolved_country = None
        if gliner_country:
            resolved_country = self._resolve_country(gliner_country)

        if not resolved_country:
            resolved_country = self._detect_country_fallback(query)
        t_rapidfuzz = time.perf_counter() - t0

        # SELL + "from [country]" -> the country is the user's OWN origin, not
        # a buyer filter. Applying it would force the aggregator to look for
        # buyers in the user's home country and return zero results.
        # "in [country]" with SELL is kept as a filter ("who buys X in Pakistan").
        origin_country = None
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

        # Product keyword: reuse GLiNER entities from Step 2 (no second model call).
        # GLiNER beats KeyBERT here — KeyBERT scored "wanna sugar" as a high bigram
        # because "wanna" isn't a CountVectorizer stop-word.
        cleaned_query = query
        if resolved_country:
            cleaned_query = re.sub(
                r'\b' + re.escape(resolved_country) + r'\b', ' ',
                cleaned_query, flags=re.IGNORECASE,
            )
        # Strip the raw misspelled country token too: re.sub above only matches
        # the canonical name, not the typo (e.g. 'brzail' -> Brazil).
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

        gliner_product = (
            _extract_entity(entities, "product")
            or _extract_entity(entities, "commodity")
            or _extract_entity(entities, "agricultural product")
            or _extract_entity(entities, "trade good")
        )
        if gliner_product:
            raw_product = gliner_product.strip().lower()
            # Reject GLiNER spans that are an action verb — extract_product_keyword
            # strips these correctly.
            _action_verbs = ("import", "export", "buy", "sell", "buying", "selling", "importing", "exporting")

            if raw_product in _action_verbs or raw_product.startswith(tuple(f"{v} " for v in _action_verbs)):
                logger.debug(f"[NLU] Rejected GLiNER product span {raw_product!r} (contains action verb)")
                product_keyword = None
            else:
                # Only reject as a country if the span is long enough that a high
                # fuzz score is meaningful — short tokens like 'urea' fuzzy-match
                # 'Korea' at ~67 with the old cutoff and got falsely deleted.
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

        # Pure-Python post-processing on entities, no model inference.
        t_pick_product = time.perf_counter() - t0

        # Skip the 4s OpenRouter call if regex already extracted a numeric range.
        t0 = time.perf_counter()

        has_numbers        = bool(re.search(r'\d', query))
        has_price_operator = _detect_price_operator(query)
        ranking_word_hit   = any(
            w in query.lower()
            for w in {"cheap", "cheapest", "bulk", "premium", "affordable",
                      "best price", "low price", "reliable"}
        )
        
        needs_llm = (has_numbers and has_price_operator) or (has_numbers and ranking_word_hit)

        regex_price = _build_price_filter_regex(query)
        if regex_price and "range" in regex_price:
            needs_llm = False

        price_filter = None

        t_llm = 0.0
        if not needs_llm:
            import copy
            llm_result  = copy.deepcopy(_LLM_UNIFIED_EMPTY)
            price_filter = regex_price
        else:
            _t0_llm = time.perf_counter()
            llm_result = _call_llm_unified(query)
            t_llm = time.perf_counter() - _t0_llm
            price_filter = _price_filter_from_llm(llm_result)

        quantity     = llm_result.get("quantity")
        llm_product  = llm_result.get("product")

        if not product_keyword and llm_product:
            product_keyword = llm_product
            product_method  = "llm"

        if not product_keyword:
            product_keyword = extract_product_keyword(cleaned_query)
            product_method  = "stopword"

        # Residual preposition cleanup: GLiNER/LLM sometimes return "suggar from"
        # as the product span. Strip the stray preposition.
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

        # Strip garbled trade verbs from multi-word keywords. Single-word typos
        # are left for the product resolver's PASS 4/5.
        if product_keyword:
            _stripped = strip_noise_tokens(product_keyword)
            if _stripped != product_keyword:
                logger.debug(
                    f"[NLU] Noise strip: {product_keyword!r} → {_stripped!r}"
                )
                product_keyword = _stripped

        # Cutoff 88 (raised from 65) blocks urea->Korea / iron->Iran false positives.
        # Well-known country names still resolve via direct catalog lookup, which
        # ignores the cutoff.
        if product_keyword and len(product_keyword.split()) > 1:
            _kw_words = product_keyword.split()
            _kw_cleaned = [
                w for w in _kw_words
                if not self._resolve_country(w, cutoff=88.0)
            ]
            if _kw_cleaned and _kw_cleaned != _kw_words:
                product_keyword = ' '.join(_kw_cleaned).strip()
                logger.debug(f"[NLU] Country token removed from product: {_kw_words} → {product_keyword!r}")

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

        # Single-word spell-correct via RapidFuzz against the product catalog,
        # cached on the instance so the DB query runs only once per worker.
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

        os_filter = _build_perspective_filter(intent, ui_context, resolved_country)
        if price_filter:
            os_filter.setdefault("bool", {}).setdefault("must", []).append(price_filter)

        # Ranking hint runs on the raw query to catch all signals.
        ranking_hint = _detect_ranking_hint(query)
        price_filter_hint = (price_filter or {}).get("ranking_hint")
        if price_filter_hint and not ranking_hint:
            ranking_hint = price_filter_hint

        result = {
            "intent":          intent,
            "product":         product_keyword,
            "product_keyword": product_keyword,
            "country":         resolved_country,
            "origin_country":  origin_country,  # SELL-from queries; not a DB filter
            "quantity":        quantity,
            "price_filter":    price_filter,
            "ranking_hint":    ranking_hint,
            "os_filter":       os_filter,
            "entities":        entities,
            "ui_context":      ui_context,
            "timings": {
                "setfit": t_setfit,
                "gliner": t_gliner,
                "rapidfuzz": t_rapidfuzz,
                "pick_product": t_pick_product,
                "total": time.perf_counter() - t_nlu_total,
            }
        }

        return result

    def get_search_filters(self, query: str, ui_context: str = "import") -> dict:
        return self.parse(query, ui_context=ui_context)

    def _resolve_country(self, raw_country: str, cutoff: float = 75.0) -> Optional[str]:
        # Block meta-words before they reach RapidFuzz.
        STOPWORDS = {
            "countries", "country", "international", "global", "worldwide", "abroad",
            "all", "any", "some", "which", "what", "where", "who", "how", "the", "for",
            "can", "get", "want", "wanna", "need", "please", "pls", "yo", "me", "us",
            "find", "show", "give", "tell", "help", "let", "make", "do", "go",
            "in", "to", "no",
        }
        if raw_country.lower().strip() in STOPWORDS:
            return None

        # Direct lookup handles abbreviations like 'pak', 'uae'.
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
        q = query.lower()

        # Multi-word prepositions must come first so "based in brazil" matches
        # before the single-word "in brazil" pattern.
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
            "where", "who", "what", "which", "how",
            "anywhere", "somewhere", "wherever", "any country", "anyplace", "any",
            "maybe", "perhaps", "possibly", "idk", "not sure"
        )

        has_preposition = re.search(r'\b(?:from|frm|fron|form|in|based\s+in|located\s+in|within)\b', q)

        for pattern in _PREP_PATTERNS:
            m = re.search(pattern, q)
            if m:
                candidate = m.group(1).strip()

                if candidate.startswith(_FORBIDDEN_PREFIXES):
                    continue

                _direct = _COUNTRY_CATALOG.get(candidate.lower())
                if _direct:
                    return _direct

                resolved = self._resolve_country(candidate, cutoff=65.0)
                if resolved:
                    return resolved
                return None

        # Free token scan is skipped when a preposition exists — the anchored pass
        # had its chance and falling through caused false positives like
        # 'brzail' -> 'Anguilla' via a spurious short-key match.
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


def verify_nlu_performance():
    """Run directly: python -m search.services.nlu_engine"""
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
