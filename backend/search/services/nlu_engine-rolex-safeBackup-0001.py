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
# Matches the output path in search/services/train_intent.py
_INTENT_MODEL_PATH = _BACKEND_DIR / "search" / "models" / "intent_model"

# ---------------------------------------------------------------------------
# Price operator keywords → OpenSearch range keys
# ---------------------------------------------------------------------------
_LTE_PHRASES = {
    "under", "below", "max", "less than", "cheaper than", "at most",
    "no more than", "not more than", "not exceeding", "not above",
    "maximum", "ceiling", "up to", "upto", "within", "lower than",
    "cheaper", "no greater than", "not greater than",
}
_GTE_PHRASES = {
    "above", "over", "min", "more than", "at least", "minimum",
    "greater than", "higher than", "not less than", "at minimum",
    "floor", "starting from", "starting at", "no less than",
    "not below", "not under", "exceeding", "beyond",
}

# ---------------------------------------------------------------------------
# Stop words for product keyword extraction
# These are stripped from the raw query before searching product names.
# Order matters — multi-word phrases first before single words.
# ---------------------------------------------------------------------------
_INTENT_STOP_PHRASES = [
    # ── Multi-word phrases — longest/most specific first ──────────────────
    # "I am ..." forms
    "i am currently looking to buy", "i am currently looking to sell",
    "i am interested in buying", "i am interested in selling",
    "i am interested in importing", "i am interested in exporting",
    "i am interested in purchasing",
    "i am looking to buy", "i am looking to sell",
    "i am looking to import", "i am looking to export",
    "i am looking for buyers of", "i am looking for sellers of",
    "i am looking for suppliers of",
    "i am searching for", "i am seeking",
    "i am in need of", "i am in search of",
    # "I would like ..." forms
    "i would like to buy", "i would like to sell",
    "i would like to import", "i would like to export",
    "i would like to purchase", "i would like to source",
    "i would like to procure",
    # "I want/need ..." forms
    "i wanna buy", "i wanna sell",
    "i want to buy", "i want to sell",
    "i want to import", "i want to export",
    "i want to purchase", "i want to procure",
    "i need to buy", "i need to sell",
    "i need to import", "i need to export",
    "i need to purchase",
    "i want", "i need",
    # "Interested in ..." forms (without leading "I am")
    "interested in buying", "interested in selling",
    "interested in importing", "interested in exporting",
    "interested in purchasing", "interested in sourcing",
    "interested in procuring",
    "interested in",
    # "Looking ..." forms
    "looking to buy", "looking to sell",
    "looking to import", "looking to export",
    "looking to source", "looking to procure",
    "looking for buyers of", "looking for sellers of",
    "looking for suppliers of", "looking for",
    # "Find ..." forms
    "find buyers for", "find sellers for", "find suppliers for",
    "find buyers of", "find sellers of", "find suppliers of",
    "find me",
    # "Can you ..." / "Help me ..." forms
    "can you help me find", "can you find me", "can you show me",
    "can you provide", "can you suggest",
    "help me find", "help me source",
    "show me",
    # "Search / Get ..." forms
    "get the product called", "get me",
    "search for suppliers of", "search for buyers of", "search for",
    "im looking for", "i am looking for",
    # "Want/Need to ..." (without leading "I")
    "want to buy", "want to sell", "want to import", "want to export",
    "want to purchase", "want to procure", "want to source",
    "need to buy", "need to sell", "need to import", "need to export",
    "need to purchase", "need to source",
    # "Where/How/Who ..." forms
    "where do i get", "where can i buy", "where can i get", "where do i buy",
    "where can i find", "where can i source",
    "how do i get", "how can i buy", "how can i source",
    "where to buy", "where to find", "where to source", "where to get",
    "who sells", "who buys", "who supplies", "who is selling", "who is buying",
    "who can supply", "who can provide", "who manufactures", "who produces",
    "is there anyone selling", "is there anyone buying",
    # "Any ..." forms
    "any supplier of", "any buyer of", "any seller of",
    "any importer of", "any exporter of",
    # Noun-phrase forms
    "suppliers of", "buyers of", "sellers of", "importers of", "exporters of",
    "manufacturers of", "producers of", "distributors of", "vendors of",
    "import of", "export of", "source of", "supply of",
    # "We ..." forms (company queries)
    "we are looking for", "we are interested in buying", "we are interested in",
    "we are searching for", "we are seeking",
    "we need", "we want", "we require", "we are looking to buy",
    "we are looking to import", "we are looking to source",
    "our company needs", "our company wants", "our company requires",
    "our company is looking for", "our firm needs", "our firm requires",
    "our organization needs", "our organization requires",
    # Polite/formal forms
    "kindly provide", "kindly send", "kindly share",
    "please provide", "please send", "please share",
    "please help me find", "please suggest",
    "request for quotation for", "request for quote for",
    "seeking quotation for", "seeking quote for",
    "require quotation for", "require quote for",
    "need quotation for", "need quote for",
    # Urgency + context phrases
    "urgent requirement for", "urgently need", "urgent need",
    "urgently require", "urgent requirement of",
    "requirement for", "requirement of",
    "in need of", "in search of", "in market for",
    # ── Single words last ─────────────────────────────────────────────────
    "where", "how", "what", "which",
    "buy", "sell", "purchase", "import", "export", "get",
    "supplier", "suppliers", "buyer", "buyers", "seller", "sellers",
    "importer", "importers", "exporter", "exporters",
    "manufacturer", "manufacturers", "producer", "producers",
    "distributor", "distributors", "vendor", "vendors",
    "find", "search", "looking", "please", "need", "required",
    "kindly", "urgently", "urgent",
    "interested", "require", "seek", "source", "procure",
    "for", "me", "best", "good", "quality",
    "wholesale", "retail", "direct",
    "rate", "rates", "price", "prices", "quote", "quotation",
    "inquiry", "enquiry", "enquiries",
    "of", "from", "at", "by", "with", "the", "a", "an",
    "in", "to", "and", "or",
    "are", "is", "was", "we", "our", "i",
    "currently", "immediately", "asap",
    # Corporate noise words that survive phrase stripping
    "company", "companies", "firm", "business", "organization",
    "factory", "plant", "office",
    # Unit and currency noise
    "usd", "pkr", "eur", "gbp", "percent", "pct",
    "ton", "tons", "tonne", "tonnes", "kg", "kilogram",
    "mt", "metric", "per", "unit", "units",
]

# ---------------------------------------------------------------------------
# KeyBERT stop words — passed to KeyBERT.extract_keywords() in parse().
# These are words KeyBERT should NOT surface as product keywords.
# Broader than _INTENT_STOP_PHRASES because KeyBERT is called AFTER the
# country is already stripped from cleaned_query, and works at word-level.
# ---------------------------------------------------------------------------
_KB_STOP = [
    # Intent verbs — base forms AND common inflections (KeyBERT checks exact lowercase match)
    "buy", "buying", "bought",
    "sell", "selling", "sold",
    "purchase", "purchasing", "purchased",
    "import", "importing", "imported",
    "export", "exporting", "exported",
    "get", "getting", "got",
    "find", "finding", "found",
    "search", "searching", "searched",
    "source", "sourcing", "sourced",
    "procure", "procuring", "procured",
    "order", "ordering", "ordered",
    "inquire", "inquiring", "enquire", "enquiring",
    "need", "needed", "needing", "needs",
    "want", "wanted", "wanting", "wants",
    "require", "requires", "requiring", "required", "requirement", "requirements",
    "seek", "seeks", "seeking", "sought",
    "provide", "provides", "providing", "provided",
    "interested", "interest",
    "looking",
    # Role nouns
    "supplier", "suppliers", "buyer", "buyers", "seller", "sellers",
    "importer", "importers", "exporter", "exporters",
    "manufacturer", "manufacturers", "producer", "producers",
    "distributor", "distributors", "vendor", "vendors",
    "company", "companies", "firm", "firms", "business", "organization",
    "factory", "factories", "plant", "plants",
    # Price / quantity noise
    "under", "above", "below", "over", "cheap", "cheaper", "cheapest",
    "affordable", "expensive", "price", "rate", "cost", "value",
    "bulk", "wholesale", "retail", "direct",
    "urgent", "urgently", "asap", "immediate", "immediately",
    "ton", "tons", "tonne", "tonnes", "kg", "kilogram", "kilograms",
    "mt", "metric", "per", "unit", "units",
    # Polite / filler words
    "please", "kindly", "urgently", "currently",
    "quotation", "quote", "inquiry", "enquiry",
    "rate", "rates", "best",
    # Prepositions and articles
    "of", "from", "at", "by", "with", "the", "a", "an", "in", "to", "for",
    "and", "or",
    "are", "is", "was", "we", "our", "i",
    # Corporate noise
    "company", "companies", "firm", "business", "organization",
    "factory", "plant", "office",
    # Currency / units (may appear after price strip misses something)
    "usd", "pkr", "eur", "gbp", "percent", "pct",
    "ton", "tons", "tonne", "tonnes", "kg", "kilogram",
    "mt", "metric", "per", "unit", "units",
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

    # Dynamic stripping of intent verbs — catches garbled/extended forms (buyyy, importttt, etc.)
    # Also strips: interested→interest\w*, require→requir\w*, seek→seek\w*, source→sourc\w*,
    # procure→procur\w*, order→order\w*, inquire→inquir\w*, enquire→enquir\w*
    q = re.sub(
        r'\b(buy\w*|sell\w*|get\w*|import\w*|export\w*|purchas\w*|procur\w*|'
        r'wanna|want\w*|interest\w*|requir\w*|seek\w*|sourc\w*|'
        r'order\w*|inquir\w*|enquir\w*|distribut\w*)\b',
        ' ', q
    )

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


_LLM_MISSING_KEY_LOGGED = False

# Cached Vertex AI credentials (refreshed automatically by google-auth)
_VERTEX_CREDS = None
_VERTEX_CREDS_LOCK = None


def _get_vertex_credentials():
    """Load service-account credentials once, reuse across requests."""
    global _VERTEX_CREDS, _VERTEX_CREDS_LOCK
    import threading
    if _VERTEX_CREDS_LOCK is None:
        _VERTEX_CREDS_LOCK = threading.Lock()
    with _VERTEX_CREDS_LOCK:
        if _VERTEX_CREDS is None:
            from django.conf import settings
            from google.oauth2 import service_account
            sa_path = getattr(settings, 'VERTEX_SA_PATH', '')
            if not sa_path:
                return None
            _VERTEX_CREDS = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            logger.info(f"[LLM] Vertex AI service-account loaded: {sa_path}")
        return _VERTEX_CREDS


def _call_vertex_gemini(system_prompt: str, user_prompt: str) -> Optional[dict]:
    """
    Call Gemini on Vertex AI via REST + service-account auth.
    Retries indefinitely on 429 (quota) with exponential back-off.
    Falls back to gemini-2.0-flash if gemini-2.0-flash-lite fails.
    """
    import json, time, requests
    from django.conf import settings
    from google.auth.transport.requests import Request as GoogleRequest

    creds = _get_vertex_credentials()
    if creds is None:
        return None

    project  = getattr(settings, 'VERTEX_PROJECT',  '')
    location = getattr(settings, 'VERTEX_LOCATION', 'global')

    if not project:
        logger.warning("[LLM] VERTEX_PROJECT_ID not set")
        return None

    # Refresh token if expired
    if not creds.valid:
        creds.refresh(GoogleRequest())

    base_url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}"
        f"/locations/{location}/publishers/google/models"
    )
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},  # disable reasoning for max speed
        },
    }

    # gemini-2.5-flash-lite: fastest (0.29s TTFT, 294 t/s), GA stable
    # gemini-2.5-flash: fallback, slightly slower but more capable
    _deadline = time.monotonic() + 12  # hard wall-clock budget for the entire Vertex call
    for model in ("gemini-2.5-flash-lite", "gemini-2.5-flash"):
        url     = f"{base_url}/{model}:generateContent"
        attempt = 0
        while True:
            if time.monotonic() > _deadline:
                logger.warning(f"[LLM] Vertex wall-clock deadline exceeded — falling back to OpenRouter")
                return None

            attempt += 1
            try:
                # Refresh token before each attempt in case it expired mid-backoff
                if not creds.valid:
                    creds.refresh(GoogleRequest())
                    headers["Authorization"] = f"Bearer {creds.token}"

                remaining = max(1.0, _deadline - time.monotonic())
                resp = requests.post(url, headers=headers, json=payload, timeout=min(10, remaining))

                if resp.status_code == 429:
                    wait = min(2 ** attempt, 4)  # cap backoff at 4s; total budget enforced by deadline
                    logger.warning(f"[LLM] Vertex 429 on {model} (attempt {attempt}) — retrying in {wait}s")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                content = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if content.startswith("```json"):
                    content = content[7:].rstrip("` \n")
                elif content.startswith("```"):
                    content = content[3:].rstrip("` \n")
                result = json.loads(content)
                logger.info(f"[LLM] Vertex Gemini ({model}) OK — attempt {attempt}")
                return result

            except Exception as e:
                logger.warning(f"[LLM] Vertex Gemini ({model}) attempt {attempt} failed: {e}")
                break  # non-429 error → try next model

    logger.warning("[LLM] All Vertex Gemini models failed")
    return None


def _call_openrouter_llm(system_prompt: str, user_prompt: str) -> Optional[dict]:
    """Entry point for all LLM calls. Vertex AI is primary, OpenRouter is fallback."""
    import json, requests
    from django.conf import settings

    global _LLM_MISSING_KEY_LOGGED

    # ── Primary: Vertex AI ───────────────────────────────────────────────────
    sa_path = getattr(settings, 'VERTEX_SA_PATH', '')
    if sa_path:
        result = _call_vertex_gemini(system_prompt, user_prompt)
        if result is not None:
            return result
        logger.warning("[LLM] Vertex AI failed — falling back to OpenRouter")

    # ── Fallback: OpenRouter ─────────────────────────────────────────────────
    api_key = getattr(settings, 'OPENROUTER_API_KEY', '')
    if not api_key:
        if not _LLM_MISSING_KEY_LOGGED:
            logger.info("[LLM] No LLM configured — using regex/KeyBERT fallback (one-time notice)")
            _LLM_MISSING_KEY_LOGGED = True
        return None

    url     = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-lite",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        logger.warning(f"[LLM] OpenRouter failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Written-number word-to-digit conversion
# Used by _build_price_filter_regex so "eight hundred" → 800 when LLM offline.
# ---------------------------------------------------------------------------
_W2D_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_W2D_MULTS = {"hundred": 100, "thousand": 1_000, "million": 1_000_000}
_W2D_ALL   = set(_W2D_ONES) | set(_W2D_MULTS)
# Regex that greedily matches a run of number-words (with optional "and")
_WRITTEN_NUM_RE = re.compile(
    r'\b((?:' + '|'.join(sorted(_W2D_ALL, key=len, reverse=True)) + r')(?:\s+and\s+|\s+))*(?:'
    + '|'.join(sorted(_W2D_ALL, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)


def _words_to_number(phrase: str) -> Optional[float]:
    """
    Convert a string of English number-words to a float.
    "eight hundred"    → 800.0
    "one thousand five hundred" → 1500.0
    Returns None if any word is unrecognised.
    """
    tokens = re.sub(r'\band\b', ' ', phrase.lower()).split()
    total, current = 0, 0
    for tok in tokens:
        if tok in _W2D_ONES:
            current += _W2D_ONES[tok]
        elif tok == "hundred":
            current = (current or 1) * 100
        elif tok in ("thousand", "million"):
            mult = _W2D_MULTS[tok]
            total = (total + (current or 1)) * mult
            current = 0
        else:
            return None
    total += current
    return float(total) if total > 0 else None


def _normalize_written_numbers(text: str) -> str:
    """
    Replace number-word sequences in text with their digit equivalents.
    "sugar under eight hundred usd" → "sugar under 800 usd"
    """
    def _replace(m: re.Match) -> str:
        val = _words_to_number(m.group(0))
        return str(int(val)) if val is not None else m.group(0)
    return _WRITTEN_NUM_RE.sub(_replace, text)


def _build_price_filter_regex(raw_query: str) -> Optional[dict]:
    """
    Regex-based price extraction — used as fallback when LLM is unavailable.
    Handles:
      - Digit patterns:   'under 800', 'below $500', 'above 1000 usd'
      - Written numbers:  'under eight hundred', 'above one thousand'
      - Symbol operators: 'sugar < $500', 'price > 1000'
      - Ranking signals:  'cheap', 'bulk', 'premium' (no number)
    """
    q = raw_query.lower()

    # Detect ranking-only signals (no number present)
    price_asc_words  = {
        "cheap", "cheapest", "cheaply", "affordable", "affordably",
        "budget", "budget friendly", "budget-friendly",
        "low price", "low prices", "low cost", "low-cost", "low rate",
        "best price", "best rate", "best deal", "good deal",
        "inexpensive", "economical", "economically", "cost effective", "cost-effective",
        "reasonable", "reasonably priced", "reasonably", "reasonable rate",
        "bargain", "discount", "discounted", "discounts",
        "value for money", "competitive price", "competitive rate",
    }
    price_desc_words = {
        "bulk", "premium", "grade a", "grade-a", "top grade",
        "high quality", "high-quality", "superior quality",
        "first class", "first-class", "top quality",
        "reliable", "reputable", "trusted", "verified", "certified",
        "established", "well established", "well-established",
        "top supplier", "leading supplier", "large quantity", "high volume",
        "industrial grade", "industrial-grade", "commercial grade",
        "organic",
    }
    has_number = bool(re.search(r'\d', q)) or bool(_WRITTEN_NUM_RE.search(q))
    if not has_number:
        if any(w in q for w in price_asc_words):
            logger.debug("[RegexPrice] No-number price_asc signal → ranking_hint=price_asc only")
            return {"ranking_hint": "price_asc"}
        if any(w in q for w in price_desc_words):
            logger.debug("[RegexPrice] No-number price_desc signal → ranking_hint=price_desc only")
            return {"ranking_hint": "price_desc"}

    # Normalise written numbers before the digit patterns run.
    # "sugar under eight hundred" → "sugar under 800"
    q = _normalize_written_numbers(q)
    logger.debug(f"[RegexPrice] after written-num normalisation: {q!r}")

    # Symbol operators: 'sugar < $500', 'price >= 1000', 'cost ≤ 700'
    sym_lte = re.search(r'(?:<=?|≤)\s*\$?([\d,]+(?:\.\d+)?)', q)
    if sym_lte:
        val = float(sym_lte.group(1).replace(',', ''))
        logger.debug(f"[RegexPrice] symbol-lte detected: ceiling={val}")
        return {"range": {"usd_per_mt": {"lte": val}}, "ranking_hint": "price_asc"}

    sym_gte = re.search(r'(?:>=?|≥)\s*\$?([\d,]+(?:\.\d+)?)', q)
    if sym_gte:
        val = float(sym_gte.group(1).replace(',', ''))
        logger.debug(f"[RegexPrice] symbol-gte detected: floor={val}")
        return {"range": {"usd_per_mt": {"gte": val}}, "ranking_hint": None}

    # Word-form operators
    lte_pattern   = (
        r'\b(?:under|below|less than|cheaper than|no more than|not more than|'
        r'at most|max|maximum|not exceed(?:ing)?|up to|upto|within|'
        r'lower than|not above|no greater than|ceiling)\s*\$?([\d,]+(?:\.\d+)?)'
    )
    gte_pattern   = (
        r'\b(?:above|over|more than|at least|minimum|min|greater than|higher than|'
        r'not less than|at minimum|floor|starting from|starting at|no less than|'
        r'not below|not under|exceeding|beyond)\s*\$?([\d,]+(?:\.\d+)?)'
    )
    range_pattern = r'\b(?:around|roughly|approximately|about|near|close to)\s*\$?([\d,]+(?:\.\d+)?)'

    m = re.search(lte_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        logger.debug(f"[RegexPrice] lte detected: ceiling={val}")
        return {"range": {"usd_per_mt": {"lte": val}}, "ranking_hint": "price_asc"}

    m = re.search(gte_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        logger.debug(f"[RegexPrice] gte detected: floor={val}")
        return {"range": {"usd_per_mt": {"gte": val}}, "ranking_hint": None}

    m = re.search(range_pattern, q)
    if m:
        val = float(m.group(1).replace(',', ''))
        tol = 0.15
        logger.debug(f"[RegexPrice] range detected: center={val} tol={tol}")
        return {"range": {"usd_per_mt": {"gte": val * (1 - tol), "lte": val * (1 + tol)}}, "ranking_hint": None}

    return None


_LLM_UNIFIED_PROMPT = '''\
You are a query parser for ZaraiLink, a B2B commodity trade platform.
Extract structured info from a trade search query. Return ONLY valid JSON.

Rules:
- products: array of up to 2 product keywords. Spell-correct obvious typos ("suagr"->"sugar", "cotten"->"cotton", "ureea"->"urea"). Strip ONLY intent/role words (buy/sell/import/export/need/want/find/get/source/supplier/buyer). KEEP all grade, type, and specification qualifiers as they are part of the product identity.
  Examples: "I want to buy suagr" -> ["sugar"]. "refined sugar importers" -> ["refined sugar"]. "dextrose anhydrous" -> ["dextrose anhydrous"]. "import wheat and rice from China" -> ["wheat","rice"]. "find urea 46-0-0 suppliers" -> ["urea 46-0-0"]. "lactose monohydrate" -> ["lactose monohydrate"]. [] if no product found.
- country: full English country name if mentioned, null otherwise.
- price.operator: "lte" (under/below/max/cheap/affordable/at most), "gte" (above/min/premium/at least), null if none.
- price.value: number only. Written numbers ("eight hundred") -> 800. null if none.
- price.currency: "USD" if price present but currency unclear, null if no price.
- price.ranking_hint: "price_asc" if cheapest/lowest price wanted, "price_desc" if bulk/premium/best quality wanted, null otherwise. Note: "best quality" alone is price_desc, but "best quality below $X" has both lte operator AND price_desc.
- quantity: raw string as typed, null if none.

Return ONLY this JSON, no extra text:
{"products":[],"country":null,"price":{"operator":null,"value":null,"currency":null,"ranking_hint":null},"quantity":null}
'''

_LLM_UNIFIED_EMPTY: dict = {
    "products": [],
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

        result = copy.deepcopy(_LLM_UNIFIED_EMPTY)
        # Support both old "product" (string) and new "products" (array) fields
        raw_products = parsed.get("products") or []
        if not raw_products and parsed.get("product"):
            raw_products = [parsed["product"]]
        result["products"] = [p for p in raw_products if p and str(p).strip()][:2]
        result["country"]  = parsed.get("country") or None
        result["quantity"] = parsed.get("quantity") or None
        price_raw = parsed.get("price") or {}
        result["price"] = {
            "operator":     price_raw.get("operator"),
            "value":        price_raw.get("value"),
            "currency":     price_raw.get("currency"),
            "ranking_hint": price_raw.get("ranking_hint"),
        }
        logger.info(f"[LLM] Unified parse OK: product={result.get('products')} country={result.get('country')} price={result.get('price')}")
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
# Feature flags
# ===========================================================================

# Set True  → GLiNER loads at startup and is used as last-resort country extractor.
# Set False → GLiNER is skipped entirely (saves ~300 MB RAM + 3-5 s startup time).
#             Country detection still works via FALLBACK_COUNTRIES dict, LLM hint,
#             and RapidFuzz. Only rare country names in complex sentences are lost.
_GLINER_ENABLED = False  # ← change this one line to re-enable GLiNER


# ===========================================================================
# ModernNLUEngine
# ===========================================================================

class ModernNLUEngine:
    """
    NLU Engine — LLM-primary architecture.

    Extraction priority (highest to lowest):
      Product  : LLM → KeyBERT → stop-word strip
      Country  : FALLBACK_COUNTRIES dict → LLM hint → GLiNER (if enabled) → RapidFuzz
      Price    : LLM → regex fallback
      Quantity : LLM only
      Intent   : SetFit → pattern rules → keyword regex → default BUY

    When OPENROUTER_API_KEY is set, the LLM call handles product + country + price
    + quantity in a single request. KeyBERT, regex, and GLiNER serve as offline
    fallbacks for when the LLM is unavailable or returns null for a field.
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
        """Load SetFit model if present. Silently uses regex fallback otherwise.

        The regex intent detector (see predict_intent) is >95% accurate on
        trade-domain BUY/SELL queries since users almost always use explicit
        verbs ("buy", "sell", "import", "export", "supplier", "buyer"). The
        SetFit model only adds marginal accuracy on ambiguous phrasing, so
        running without it is a fully supported mode — not an error.
        """
        if cls._intent_model is not None:
            return

        model_path = str(_INTENT_MODEL_PATH.resolve())

        # Accept any of these markers to confirm the model was saved properly
        markers = ["config_setfit.json", "model_head.pkl", "config.json"]
        model_exists = any(
            os.path.exists(os.path.join(model_path, m)) for m in markers
        )

        if not model_exists:
            logger.info("[NLU] Using regex intent detector (SetFit model not trained).")
            return

        try:
            from setfit import SetFitModel
            logger.info(f"[NLU] Loading SetFit intent model from {model_path} ...")
            cls._intent_model = SetFitModel.from_pretrained(model_path)
            logger.info("[NLU] SetFit model loaded successfully.")
        except Exception as e:
            logger.warning(f"[NLU] SetFit load failed ({e}); falling back to regex intent detector.")

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
        """Load GLiNER for country extraction (last-resort fallback).
        Skipped entirely when _GLINER_ENABLED = False.
        """
        if not _GLINER_ENABLED:
            logger.info("[NLU] GLiNER disabled (_GLINER_ENABLED=False). Country detection via dict + LLM + RapidFuzz.")
            return
        if cls._ner_model is not None:
            return
        try:
            from gliner import GLiNER
            logger.info("[NLU] Loading GLiNER model: urchade/gliner_base ...")
            cls._ner_model = GLiNER.from_pretrained("urchade/gliner_base")
            logger.info("[NLU] GLiNER loaded.")
        except Exception as e:
            logger.info(f"[NLU] GLiNER not available — country detection via dict + LLM + RapidFuzz: {e}")

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
          1. High-confidence pattern rules — catch semantic reversals like
             "looking for sellers of X" (= BUY) that confuse ML models trained
             on few-shot data. These patterns are precise, so they override
             SetFit when they match.
          2. SetFit ML model  — handles the long tail of ambiguous phrasings.
          3. Keyword regex    — fast fallback for simple verbs.
          4. Default to BUY   — safe default.
        """
        q = query.lower()

        # 1. Pattern rules for semantic-reversal phrases.
        # "looking for sellers of X" means the user wants to BUY from those sellers,
        # not that they want to SELL. SetFit trained on 30 examples cannot reliably
        # learn this reversal, so we hardcode the patterns.
        _want_verb   = r'(?:find|finding|looking for|look for|need|want|seeking|searching for|search for)'
        _sell_noun   = r'(?:sellers?|suppliers?|exporters?|manufacturers?|producers?|vendors?)'
        _buy_noun    = r'(?:buyers?|importers?|consumers?|purchasers?)'

        if re.search(rf'\b{_want_verb}\s+{_sell_noun}\b', q):
            return "BUY"
        if re.search(rf'\b{_want_verb}\s+{_buy_noun}\b', q):
            return "SELL"
        if re.search(r'\bwho\s+(?:is\s+)?sell(?:s|ing)?\b', q):
            return "BUY"
        if re.search(r'\bwho\s+(?:is\s+)?buy(?:s|ing)?\b', q):
            return "SELL"

        # Urdu SELL signals: "bechna hai/he" (to sell), "buyer chahiye" (need buyer),
        # "hamare paas X hai/he" (we have X), "hamare pass X" (we have X).
        if re.search(r'\bbechna\s+(?:hai|he|hain)\b', q):
            return "SELL"
        if re.search(r'\bbuyer(?:s)?\s+chahiye\b', q):
            return "SELL"
        if re.search(r'\bhamare?\s+(?:paas?|pass)\b', q):
            return "SELL"

        # BUY signals: formal procurement language that sounds like SELL to ML models.
        # "procure", "procurement", "sourcing", "rfq" are all buyer actions.
        if re.search(r'\b(?:rfq|request\s+for\s+quot(?:e|ation)|procur\w+|sourcing)\b', q):
            if not re.search(r'\b(?:sell\w*|export\w*|offer\w*|for\s+sale)\b', q):
                return "BUY"
        # "request quotation(s)" alone = buyer asking for prices, regardless of phrasing
        if re.search(r'\brequest\s+quotation\w*\b', q):
            return "BUY"

        # BUY signals: "our company requires/needs X" — unambiguous procurement intent
        if re.search(r'\b(?:our\s+(?:company|firm|organization|factory)\s+)?(?:requires?|needs?|requirement\s+for)\b', q):
            # Only if no explicit SELL verb is present
            if not re.search(r'\b(?:sell|selling|sold|offer|supply|for\s+sale|available|export)\b', q):
                return "BUY"

        # Additional SELL signals not covered by the pattern rules above.
        # "for sale" / "on sale" — user has something to sell
        if re.search(r'\bfor\s+sale\b', q):
            return "SELL"
        # "we have X", "we are selling X" — user is offering product
        if re.search(r'\bwe\s+(?:have|are\s+(?:selling|offering|supplying)|sell|supply|offer|produce|manufacture)\b', q):
            return "SELL"
        # "I am a supplier/seller/exporter" — user identifies as seller
        if re.search(r"\bi\s+(?:am|'?m)\s+(?:a\s+)?(?:seller|supplier|exporter|producer|manufacturer|vendor)\b", q):
            return "SELL"
        # "X in stock" / "stock to sell/offload" / "available for sale"
        if re.search(r'\b(?:in\s+stock|stock\s+to\s+(?:sell|offload)|available\s+for\s+(?:sale|export)|to\s+offload|our\s+stock|have\s+stock)\b', q):
            return "SELL"

        # High-confidence patterns that must override SetFit (placed after explicit SELL signals
        # so they don't conflict, but before SetFit so they can't be overridden by ML).

        # SELL: "buy(ing) our [product]" — possessive marks user as the product owner
        # e.g. "find companies interested in buying our wheat"
        # e.g. "find someone who wants to buy our cotton"
        if re.search(r'\bbuy(?:ing)?\s+our\b', q):
            return "SELL"

        # BUY: "[product] seller/supplier find me" — reversed word order, user seeks a seller
        # e.g. "cotton seller find me"
        if re.search(r'\b(?:seller|supplier|exporter)\s+find\s+me\b', q):
            return "BUY"

        # SELL: bare "export" as an action verb (exact word, not "exporters"/"exporting")
        # without any BUY-side context — e.g. "sugar export", "wheat export"
        # Guard: skip when the query contains BUY-side verbs like find/buy/import/need/want
        if re.search(r'\bexport\b', q):
            if not re.search(r'\b(?:buy|buying|import|need|want|looking|find|get|purchas|sourc)\b', q):
                return "SELL"

        # 2. SetFit model
        if self._intent_model is not None:
            try:
                pred = self._intent_model.predict([query])[0]
                if isinstance(pred, str):
                    label = pred.upper()
                else:
                    label = "BUY" if int(pred) == 0 else "SELL"

                # Guard: SetFit is miscalibrated on bare commodity queries (e.g. "wheat" → SELL).
                # If SetFit says SELL but the query has no real SELL signal, override to BUY.
                # Most ZaraiLink users are importers, so BUY is the safe default.
                if label == "SELL" and not re.search(
                    r'\b(sell\w*|export\w*|distribut\w*|supply|supplies|supplying|supplied|'
                    r'offer\w*|manufactur\w*|produc\w*|for\s+sale|available|'
                    r'stock|we\s+have|we\s+sell|we\s+produce|we\s+export)\b', q
                ):
                    logger.debug("[NLU] SetFit predicted SELL but no SELL signal found — overriding to BUY")
                    label = "BUY"

                if label in ("BUY", "SELL"):
                    return label
            except Exception as e:
                logger.warning(f"[NLU] SetFit inference failed: {e}. Using regex fallback.")

        # 3. Keyword regex fallback
        if re.search(r'\b(sell\w*|export\w*|distribut\w*|buyer\w*)\b', q):
            return "SELL"
        if re.search(r'\b(buy\w*|import\w*|get\w*|purchas\w*|need\w*|supplier\w*)\b', q):
            return "BUY"

        # 3. Default
        return "BUY"

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
        # HS CODE FAST PATH
        # If the entire query is a digit/dot pattern (e.g. "1702.3090", "17021990"),
        # treat it as an HS code and bypass the full NLU pipeline.
        # The caller (execute_search) picks up "is_hs_query=True" and passes the
        # value as hs_code to _resolve_subcategories, enabling direct DB lookup.
        # ==================================================================
        # HS code detection: normalize spaced/dashed formats before matching.
        # Handles: "1702.3090", "17021990", "1702 30 90", "17-02-30-90", "1702.30.90"
        # Also strips common prefixes: "HS code 1701", "hs 1701", "tariff 1701", "HTS 1701"
        _hs_query = re.sub(
            r'(?i)^(hs\s*code|hs|hts|tariff\s*code|tariff|heading|chapter\s*\d+\s*commodity)\s*',
            '', query.strip()
        ).strip()
        _hs_candidate = re.sub(r'[\s\-]', '', _hs_query)
        _hs_candidate = re.sub(r'\.', '', _hs_candidate)  # strip dots for length check
        _is_hs = (
            re.match(r'^[\d.]+$', _hs_query) or
            (re.match(r'^[\d\s\-\.]+$', _hs_query) and 4 <= len(_hs_candidate) <= 10)
        )
        if _is_hs:
            # Normalise HS code.
            # Spaced/dashed groups → dots: "1702 30 90" or "1702-30-90" → "1702.30.90"
            # Already dotted or bare digits → keep as-is: "1702.3" → "1702.3", "170230" → "170230"
            if re.search(r'[\s\-]', _hs_query):
                _hs_parts = [p for p in re.split(r'[\s\-]+', _hs_query.strip()) if p]
                # If every part is exactly 2 digits (e.g. "17 01"), the user typed the
                # 4-digit heading as two separate 2-digit groups — concatenate them.
                # Otherwise (e.g. "1702 30 90"), use standard dot-notation.
                if all(len(p) == 2 and p.isdigit() for p in _hs_parts):
                    _hs_normalised = ''.join(_hs_parts)
                else:
                    _hs_normalised = '.'.join(_hs_parts)
            else:
                _hs_normalised = _hs_query
            logger.info(f"[NLU] HS code query detected: {query.strip()!r} → normalised: {_hs_normalised!r}")
            return {
                "intent":          "BUY",
                "product":         _hs_normalised,
                "product_keyword": _hs_normalised,
                "country":         None,
                "quantity":        None,
                "price_filter":    None,
                "os_filter":       _build_perspective_filter("BUY", ui_context, None),
                "entities":        [],
                "ui_context":      ui_context,
                "is_hs_query":     True,
            }

        # ==================================================================
        # STEP 1 — Intent Detection
        # SetFit model is primary; regex is the fallback.
        # ==================================================================
        t0 = time.perf_counter()
        intent = self.predict_intent(query)
        logger.debug(f"[TIMING NLU] SetFit intent: {time.perf_counter() - t0:.3f}s")
        logger.debug(f"[NLU] Step1 intent={intent!r} query={query!r}")

        # ==================================================================
        # STEP 2 — LLM: PRIMARY extractor for product, country, price, quantity.
        # When OPENROUTER_API_KEY is set, a single API call returns all four fields
        # as structured JSON. Everything below is fallback for when LLM is absent
        # or returns null for a particular field.
        # When no API key is set, _call_llm_unified returns _LLM_UNIFIED_EMPTY
        # instantly (no network call) and the offline path handles everything.
        # ==================================================================
        t0 = time.perf_counter()
        llm_result   = _call_llm_unified(query)
        llm_products = llm_result.get("products") or []
        llm_product  = llm_products[0] if llm_products else None   # primary
        llm_product2 = llm_products[1] if len(llm_products) > 1 else None  # secondary
        llm_country  = llm_result.get("country")
        quantity     = llm_result.get("quantity")
        price_filter = _price_filter_from_llm(llm_result)
        logger.debug(
            f"[TIMING NLU] LLM call: {time.perf_counter() - t0:.3f}s | "
            f"products={llm_products!r} country={llm_country!r} price={llm_result.get('price')}"
        )

        # ==================================================================
        # STEP 3 — Country Resolution
        # Layer 1: Fast regex/dict lookup — always runs, no model needed.
        # Layer 2: LLM country hint (when LLM worked and dict missed).
        # Layer 3: GLiNER span extraction — last resort (only when _GLINER_ENABLED).
        # ==================================================================
        resolved_country = self._detect_country_fallback(query)

        if not resolved_country and llm_country:
            resolved_country = self._resolve_country(llm_country)
            logger.debug(f"[NLU] Country resolved via LLM hint: {resolved_country!r}")

        entities = []
        if not resolved_country and self._ner_model is not None:
            entities = self.extract_entities(query)
            gliner_country = (
                _extract_entity(entities, "country")
                or _extract_entity(entities, "location")
            )
            if gliner_country:
                resolved_country = self._resolve_country(gliner_country)
                logger.debug(f"[NLU] Country resolved via GLiNER: {resolved_country!r}")

        logger.debug(f"[NLU] Step3 resolved_country={resolved_country!r}")

        # ==================================================================
        # SCOPE INFERENCE
        # Override ui_context from query signals (_infer_scope is always active).
        # When _SCOPE_TOGGLE_ENABLED on the frontend, the user-chosen scope reaches
        # here as ui_context; _infer_scope only overrides it when a strong signal
        # is present in the query text.
        # ==================================================================
        inferred_scope = self._infer_scope(query, resolved_country)
        if inferred_scope:
            logger.debug(f"[NLU] Scope inferred from query: {inferred_scope!r} (was {ui_context!r})")
            ui_context = inferred_scope

        # ==================================================================
        # STEP 4 — Product Keyword
        # Strip resolved country from query before keyword extraction.
        # Priority: LLM product (Step 2) → KeyBERT (fallback) → stop-word strip (last resort)
        # ==================================================================
        cleaned_query = query
        if resolved_country:
            cleaned_query = re.sub(
                r'\b' + re.escape(resolved_country) + r'\b', ' ',
                cleaned_query, flags=re.IGNORECASE,
            )

        product_keyword  = llm_product   # LLM is primary
        product_keyword2 = llm_product2  # secondary (may be None)
        product_method   = "llm" if llm_product else "none"

        if not product_keyword and self._keyword_model is not None:
            t0 = time.perf_counter()
            try:
                kw_results = self._keyword_model.extract_keywords(
                    cleaned_query,
                    keyphrase_ngram_range=(1, 2),
                    stop_words=_KB_STOP,
                    top_n=1,
                )
                if kw_results:
                    product_keyword = kw_results[0][0]
                    product_method  = "keybert"
            except Exception as e:
                logger.warning(f"[NLU] KeyBERT extraction failed: {e}")
            logger.debug(f"[TIMING NLU] KeyBERT fallback: {time.perf_counter() - t0:.3f}s product={product_keyword!r}")

        if not product_keyword:
            kw = extract_product_keyword(cleaned_query)
            # Discard the fallback if it's just the raw query echoed back
            # (happens when LLM returns empty and stopword stripping removes nothing).
            if kw and kw.lower() != cleaned_query.lower().strip():
                product_keyword = kw
                product_method  = "stopword"

        logger.debug(f"[NLU] Step4 final product={product_keyword!r} via={product_method}")

        # ==================================================================
        # STEP 5 — Price filter fallback
        # Regex handles all cases when LLM was unavailable or returned no price.
        # ==================================================================
        if price_filter is None:
            price_filter = _build_price_filter_regex(query)

        # ==================================================================
        # Build OS/ORM filters (uses final ui_context after scope inference)
        # ==================================================================
        os_filter = _build_perspective_filter(intent, ui_context, resolved_country)
        if price_filter:
            os_filter.setdefault("bool", {}).setdefault("must", []).append(price_filter)

        result = {
            "intent":            intent,
            "product":           product_keyword,
            "product_keyword":   product_keyword,
            "product_keyword2":  product_keyword2,   # second product if mentioned
            "country":           resolved_country,
            "quantity":          quantity,
            "price_filter":      price_filter,
            "os_filter":         os_filter,
            "entities":          entities,
            "ui_context":        ui_context,
        }

        logger.info(
            f"[NLU] Final parse | intent={intent} | scope={ui_context} | "
            f"product={product_keyword!r} | product2={product_keyword2!r} | "
            f"country={resolved_country!r} | price={llm_result.get('price')} | "
            f"quantity={quantity!r} | product_method={product_method}"
        )
        logger.debug(f"[TIMING NLU] Total NLU: {time.perf_counter() - t_nlu_total:.3f}s")
        return result

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
            
        # FIX: Expanded from 27 to 80+ countries. The original list missed Bangladesh,
        # Philippines, Myanmar, Morocco, Russia, Netherlands, Iran, and many others.
        STANDARD_COUNTRIES = [
            "Pakistan", "China", "United States", "India", "Afghanistan",
            "United Arab Emirates", "Saudi Arabia", "Germany", "United Kingdom",
            "Australia", "Canada", "Singapore", "Malaysia", "Indonesia",
            "Turkey", "Brazil", "France", "Italy", "Spain", "Japan", "South Korea",
            "Vietnam", "Thailand", "Egypt", "South Africa", "Nigeria", "Kenya",
            "Bangladesh", "Myanmar", "Philippines", "Morocco", "Hong Kong", "Taiwan",
            "Russia", "Netherlands", "Poland", "Ukraine", "Iran", "Iraq",
            "Jordan", "Kuwait", "Qatar", "Bahrain", "Oman", "Israel",
            "Mexico", "Argentina", "Colombia", "Chile", "Peru",
            "Belgium", "Switzerland", "Sweden", "Norway", "Denmark", "Finland",
            "Portugal", "Greece", "Czech Republic", "Romania", "Hungary",
            "New Zealand", "Sri Lanka", "Nepal", "Kazakhstan", "Uzbekistan",
            "Algeria", "Tunisia", "Libya", "Sudan", "Tanzania", "Ethiopia", "Ghana",
            "Angola", "Mozambique", "Zimbabwe", "Zambia",
            "Azerbaijan", "Georgia", "Armenia",
        ]

        match = rapidfuzz.process.extractOne(
            raw_country.lower(),
            STANDARD_COUNTRIES,
            scorer=rapidfuzz.fuzz.WRatio,
            score_cutoff=60.0,
        )
        if match:
            return match[0]
        return raw_country.capitalize()

    def _detect_country_fallback(self, query: str) -> Optional[str]:
        """
        Regex fallback to detect common countries if GLiNER misses them
        or if we want to bypass fuzzy matching for strict abbreviations (ira -> Iran).
        """
        q = query.lower()
        
        # FIX: Expanded FALLBACK_COUNTRIES to cover countries that were silently dropped
        # (Bangladesh, Philippines, Myanmar, Morocco, Russia, Netherlands, Iran etc.)
        FALLBACK_COUNTRIES = {
            "china": "China", "chinaaa": "China", "chinese": "China",
            "pakistan": "Pakistan", "pak": "Pakistan", "pakistani": "Pakistan",
            "india": "India", "indian": "India",
            "turkey": "Turkey", "turk": "Turkey", "turkiye": "Turkey",
            "turekyy": "Turkey", "turky": "Turkey", "turke": "Turkey", "turkeyy": "Turkey",
            "turkish": "Turkey",
            "usa": "United States", "america": "United States", "american": "United States", "us": "United States",
            "uk": "United Kingdom", "britain": "United Kingdom", "england": "United Kingdom", "british": "United Kingdom",
            "germany": "Germany", "german": "Germany",
            "france": "France", "french": "France",
            "italy": "Italy", "italian": "Italy",
            "spain": "Spain", "spanish": "Spain",
            "uae": "United Arab Emirates", "dubai": "United Arab Emirates",
            "saudi": "Saudi Arabia", "ksa": "Saudi Arabia",
            "iran": "Iran", "iranian": "Iran",
            "iraq": "Iraq", "iraqi": "Iraq",
            "egypt": "Egypt", "egyptian": "Egypt",
            "korea": "South Korea", "korean": "South Korea",
            "japan": "Japan", "japanese": "Japan",
            "malaysia": "Malaysia", "malay": "Malaysia",
            "vietnam": "Vietnam", "vietnamese": "Vietnam",
            # Previously missing countries:
            "bangladesh": "Bangladesh", "bangla": "Bangladesh",
            "myanmar": "Myanmar", "burma": "Myanmar",
            "philippines": "Philippines", "philippine": "Philippines",
            "morocco": "Morocco", "moroccan": "Morocco",
            "hk": "Hong Kong",
            "taiwan": "Taiwan", "taiwanese": "Taiwan",
            "russia": "Russia", "russian": "Russia",
            "netherlands": "Netherlands", "holland": "Netherlands", "dutch": "Netherlands",
            "poland": "Poland", "polish": "Poland",
            "ukraine": "Ukraine", "ukrainian": "Ukraine",
            "jordan": "Jordan", "jordanian": "Jordan",
            "kuwait": "Kuwait", "kuwaiti": "Kuwait",
            "qatar": "Qatar", "qatari": "Qatar",
            "bahrain": "Bahrain", "bahraini": "Bahrain",
            "oman": "Oman", "omani": "Oman",
            "israel": "Israel", "israeli": "Israel",
            "mexico": "Mexico", "mexican": "Mexico",
            "argentina": "Argentina", "argentinian": "Argentina",
            "colombia": "Colombia", "colombian": "Colombia",
            "brazil": "Brazil", "brazilian": "Brazil",
            "chile": "Chile", "chilean": "Chile",
            "sri lanka": "Sri Lanka", "lanka": "Sri Lanka",
            "nepal": "Nepal", "nepali": "Nepal",
            "belgium": "Belgium", "belgian": "Belgium",
            "switzerland": "Switzerland", "swiss": "Switzerland",
            "sweden": "Sweden", "swedish": "Sweden",
            "norway": "Norway", "norwegian": "Norway",
            "denmark": "Denmark", "danish": "Denmark",
            "finland": "Finland", "finnish": "Finland",
            "australia": "Australia", "australian": "Australia",
            "canada": "Canada", "canadian": "Canada",
            "singapore": "Singapore",
            "indonesia": "Indonesia", "indonesian": "Indonesia",
            "thailand": "Thailand", "thai": "Thailand",
            "afghanistan": "Afghanistan", "afghan": "Afghanistan",
            "kenya": "Kenya", "kenyan": "Kenya",
            "nigeria": "Nigeria", "nigerian": "Nigeria",
            "ghana": "Ghana", "ghanaian": "Ghana",
            "ethiopia": "Ethiopia", "ethiopian": "Ethiopia",
            "kazakhstan": "Kazakhstan",
            "uzbekistan": "Uzbekistan",
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
                "Vietnam", "Thailand", "Egypt", "South Africa", "Nigeria", "Kenya",
                "Bangladesh", "Myanmar", "Philippines", "Morocco", "Hong Kong", "Taiwan",
                "Russia", "Netherlands", "Poland", "Ukraine", "Iran", "Iraq",
                "Jordan", "Kuwait", "Qatar", "Bahrain", "Oman", "Israel",
                "Mexico", "Argentina", "Colombia", "Chile", "Peru",
                "Belgium", "Switzerland", "Sweden", "Norway", "Denmark", "Finland",
                "Portugal", "Greece", "Czech Republic", "Romania", "Hungary",
                "New Zealand", "Sri Lanka", "Nepal", "Kazakhstan", "Uzbekistan",
                "Algeria", "Tunisia", "Libya", "Sudan", "Tanzania", "Ethiopia", "Ghana",
                "Angola", "Mozambique", "Zimbabwe", "Zambia",
                "Azerbaijan", "Georgia", "Armenia",
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

    def _infer_scope(self, query: str, resolved_country: Optional[str]) -> Optional[str]:
        """
        Infer WORLDWIDE or PAKISTAN scope from query signals.
        Returns 'pakistan', 'worldwide', or None (let caller decide).

        Priority (highest first):
          1. Explicit foreign country detected → worldwide (overrides city mentions).
             e.g. "import from China for our Karachi facility" → worldwide, not pakistan.
          2. Pakistan/local city keyword → pakistan.
          3. No signal → None.
        """
        q = query.lower()

        # Foreign country wins over local city — prevents Karachi/Lahore mentions
        # from overriding a clear "import from X" intent.
        if resolved_country and resolved_country.lower() not in {"pakistan", ""}:
            return "worldwide"

        local_signals = {
            "local", "domestic", "pakistan", "pakistani",
            "karachi", "lahore", "islamabad", "faisalabad", "sialkot",
            "multan", "peshawar", "rawalpindi", "hyderabad", "quetta",
            "gujranwala", "gujrat", "sargodha",
        }
        if any(s in q for s in local_signals):
            return "pakistan"

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
