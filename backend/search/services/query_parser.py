import re
import math
import difflib
import datetime

try:
    from django.conf import settings as _dj_settings
    _USE_GLINER = getattr(_dj_settings, 'SEARCH_USE_GLINER_NER', True)
    _USE_SETFIT = getattr(_dj_settings, 'SEARCH_USE_SETFIT', True)
except Exception:
    _USE_GLINER = False
    _USE_SETFIT = False


class QueryInterpreter:
    """
    Parses natural language queries into structured intent and attributes.
    Does NOT perform retrieval or database lookups.
    """

    # Minimal hardcoded fallback — used only when the DB is unreachable at startup.
    # At runtime the full country list is loaded from Transaction.origin_country /
    # destination_country (all distinct values that have ever appeared in the data).
    _FALLBACK_COUNTRIES = [
        "Pakistan", "China", "India", "Brazil", "USA", "United States", "UAE", "Dubai",
        "Vietnam", "Thailand", "Indonesia", "Germany", "France", "UK", "United Kingdom",
        "Russia", "Turkey", "Egypt", "Saudi Arabia", "Canada", "Australia", "Malaysia",
        "Kenya", "Bangladesh", "Sri Lanka", "Japan", "Korea", "South Korea", "Afghanistan",
        # Extended fallback for the most common trade partners not in the original list
        "Italy", "Spain", "Netherlands", "Belgium", "Switzerland", "Sweden", "Norway",
        "Poland", "Ukraine", "Iran", "Iraq", "Syria", "Jordan", "Kuwait", "Oman",
        "Qatar", "Bahrain", "Yemen", "Morocco", "Algeria", "Tunisia", "Libya",
        "Sudan", "Ethiopia", "Tanzania", "Uganda", "Ghana", "Nigeria", "Ivory Coast",
        "South Africa", "Mozambique", "Zambia", "Zimbabwe",
        "Mexico", "Colombia", "Peru", "Chile", "Argentina", "Venezuela",
        "Singapore", "Malaysia", "Philippines", "Myanmar", "Cambodia", "Nepal",
        "Sri Lanka", "Maldives", "Uzbekistan", "Kazakhstan", "Azerbaijan", "Georgia",
        "New Zealand", "Papua New Guinea",
    ]

    # Populated once per process on first parse call; never expires during runtime.
    # Call invalidate_countries_cache() after bulk Transaction imports if needed.
    _countries_cache = None

    @classmethod
    def _get_countries(cls) -> list:
        """
        Return the full country list, loaded from Transaction data on first call.

        - Queries origin_country + destination_country DISTINCT from Transaction table.
        - Normalises: strips whitespace, Title Cases regular names, preserves short
          all-uppercase abbreviations (UAE, USA, UK).
        - Filters out None, empty strings, numeric/garbage entries (len < 2 or
          contains digits/non-country punctuation).
        - Result is cached for the lifetime of the process (one DB round-trip per
          worker boot). Falls back to _FALLBACK_COUNTRIES if the DB is unreachable.
        """
        if cls._countries_cache is not None:
            return cls._countries_cache

        try:
            from trade_data.models import Transaction

            origins = set(
                Transaction.objects
                .exclude(origin_country__isnull=True)
                .exclude(origin_country='')
                .values_list('origin_country', flat=True)
                .distinct()
            )
            destinations = set(
                Transaction.objects
                .exclude(destination_country__isnull=True)
                .exclude(destination_country='')
                .values_list('destination_country', flat=True)
                .distinct()
            )
            raw = origins | destinations

            seen = set()
            cleaned = []
            for name in raw:
                if not isinstance(name, str):
                    continue
                name = name.strip()
                if len(name) < 2:
                    continue
                # Reject entries that contain digits or non-country punctuation
                # (catches garbage like "N/A", "Pakistan (Karachi)", "123")
                if not re.match(r"^[A-Za-z][A-Za-z\s\-\.']*$", name):
                    continue
                # Normalise: keep short all-uppercase abbreviations as-is (UAE, USA, UK);
                # Title-case everything else ("CHINA" → "China", "saudi arabia" → "Saudi Arabia")
                if len(name) <= 4 and name.isupper():
                    normalized = name          # preserve UAE, USA, UK, etc.
                else:
                    normalized = name.title()  # Saudi Arabia, Sri Lanka, etc.
                key = normalized.lower()
                if key not in seen:
                    seen.add(key)
                    cleaned.append(normalized)

            cls._countries_cache = sorted(cleaned) if cleaned else cls._FALLBACK_COUNTRIES

        except Exception:
            # DB unavailable (migrations not run, test environment, etc.) — use fallback
            cls._countries_cache = cls._FALLBACK_COUNTRIES

        return cls._countries_cache

    @classmethod
    def invalidate_countries_cache(cls):
        """Force re-load of the country list on next parse call (e.g. after bulk imports)."""
        cls._countries_cache = None

    COUNTRY_ALIASES = {
        "us": "USA", "u.s.": "USA", "united states of america": "USA", "america": "USA",
        "uae": "UAE", "u.a.e": "UAE", "emirates": "UAE",
        "uk": "UK", "u.k.": "UK", "britain": "UK",
        "ksa": "Saudi Arabia"
    }

    # Intent Scoring (Phrase -> Score)
    # Positive for BUY, Negative for SELL (or separate scores)
    # Let's use separate scores.
    BUY_SCORES = {
        "who sells": 5, "suppliers of": 5, "supplier": 3, "find exporters": 5, "find suppliers": 5,
        "source from": 5, "buy from": 5, "i want to buy": 5, "buying": 3, "imports": 2,
        "want to import": 4, "buy": 1, "purchase": 2, "sourcing": 3, "need": 2,
        "suppliers": 3,
        # "exporters" = companies that export TO Pakistan = foreign suppliers = BUY intent
        "exporters": 3, "exporter": 3,
        # "sellers" = companies selling to Pakistani buyers = BUY intent
        "sellers": 3, "seller": 3,
    }

    SELL_SCORES = {
        "who buys": 5, "buyers for": 5, "buyer": 3, "find importers": 5, "find buyers": 5,
        "demand for": 5, "sell to": 5, "i want to sell": 5, "selling": 3, "exports": 2,
        "want to export": 4, "sell": 1, "supply": 2, "available": 2,
        "demands": 3,
        "buyers": 3, "pay": 3, "pays": 3, "paying": 3, "who pay": 5,
        "looking to sell": 5, "i have": 5, "can i sell": 5,
        "buys": 5, "export": 2,
        "give away": 5, "giving away": 5, "want to give": 4, "offload": 4, "dispose": 3,
        # "importers" = Pakistani companies that import = they are the buyers = SELL intent
        "importers": 2, "importer": 2,
    }

    # Family Parsing Keywords
    FAM_6_KEYWORDS = ["top", "best", "rank", "suggest", "recommend", "highest", "most", "paying"]
    FAM_7_KEYWORDS = ["cheapest", "lowest price", "highest demand", "demand highest",
                      "compare", "vs",
                      "which country", "which countries", "best market", "best country",
                      "most demand", "top market", "top country", "country comparison",
                      "by country", "per country", "export destinations", "import sources",
                      "buyers by country", "country breakdown", "breakdown by country",
                      "where is demand", "where is highest"]
    FAM_8_KEYWORDS = [
        "shipments", "transactions", "transaction", "history", "record", "proof",
        "verification", "evidence", "invoices", "invoice", "verify",
        "purchased before", "bought before", "past purchases", "paper trail",
        "deal evidence", "has purchased", "has bought",
        "does buy", "does purchase",
    ]
    # Noise words to strip from the product field specifically for F8 queries
    FAM_8_PRODUCT_NOISE = ["purchased", "bought", "before", "provide", "deal"]

    # Product synonym normalization: applied before all parsing so the correct
    # product term flows through BM25/FAISS matching.
    # Approximate USD conversion rates for non-USD price queries.
    # Applied when the user specifies a price in a non-USD currency.
    CURRENCY_TO_USD = {
        'pkr': 1 / 278.0,   # Pakistani Rupee
        'eur': 1.08,         # Euro
        'gbp': 1.27,         # British Pound
        'cny': 0.138,        # Chinese Yuan
        'rmb': 0.138,        # Renminbi (same as CNY)
    }

    PRODUCT_SYNONYMS = [
        (r'\bsoya\s+bean\s+oil\b', 'soybean oil'),
        (r'\bsoya\s+bean\b',       'soybean'),
        (r'\bsoya\b',              'soybean'),
        (r'\bsoy\s+bean\b',        'soybean'),
        (r'\bpottasium\b',         'potassium'),   # common typo
        (r'\bsodium\s+bi\s*carbonate\b', 'sodium bicarbonate'),
        (r'\btitanium\s+dioxyde\b', 'titanium dioxide'),  # French-influenced typo
        (r'\bdioxyde\b',            'dioxide'),
        (r'\bsodium\s+bicarb\b',   'sodium bicarbonate'),
        (r'\bpotash\b',            'potassium'),
        (r'\bcaustic\s+soda\b',    'sodium hydroxide'),
        (r'\bglucose\s+syrup\b',   'dextrose'),
        (r'\bglucose\b',           'dextrose'),
        (r'\bsaccharose\b',        'sucrose'),
        (r'\bsulphur\b',           'sulfur'),
        (r'\bglycerine\b',         'glycerol'),
        (r'\bmaize\b',             'corn'),
        (r'\bgur\b',               'jaggery'),
        (r'\bpalmolein\b',         'palm olein'),
        (r'\bpalm\s+olein\b',      'palm olein'),
    ]

    def _convert_to_usd(self, price: float, matched_text: str) -> float:
        """Convert a price to USD if the matched text contains a non-USD currency symbol."""
        text_lower = matched_text.lower()
        for currency, rate in self.CURRENCY_TO_USD.items():
            if currency in text_lower:
                return round(price * rate, 2)
        return price  # already USD ($ or 'usd') or no currency symbol

    def _normalize_query(self, query: str) -> str:
        """Apply product synonym normalization before parsing."""
        q = query
        for pattern, replacement in self.PRODUCT_SYNONYMS:
            q = re.sub(pattern, replacement, q, flags=re.IGNORECASE)
        return q

    def parse(self, query, explicit_scope=None):
        """
        Main entry point. Handles multi-intent splitting.
        explicit_scope: If provided (e.g., from frontend), overrides any scope inference.
        """
        if not query:
            return {}

        # Normalize product synonyms/typos before any parsing
        query = self._normalize_query(query)

        # 1. Multi-Intent Detection
        # Strict Splitting: Split by ';' always.
        # Split by 'and' ONLY IF the right side is "complex" (has intent keyword OR product+country)
        
        candidates = re.split(r';', query)
        if len(candidates) == 1:
             parts = re.split(r'\b(?:and|also)\b', query, flags=re.IGNORECASE)
             final_segments = []
             current_segment = parts[0]
             
             for part in parts[1:]:
                 # Check complexity of part
                 # 1. Has explicit intent keyword?
                 has_intent = self._detect_intent_score(part)[0] != 'AMBIGUOUS'

                 # 2. Or has structural family keyword (F6/F7/F8) that implies a separate query type?
                 part_lower = part.strip().lower()
                 has_structural_intent = (
                     any(kw in part_lower for kw in self.FAM_7_KEYWORDS) or
                     any(kw in part_lower for kw in self.FAM_8_KEYWORDS) or
                     any(kw in part_lower for kw in self.FAM_6_KEYWORDS)
                 )

                 # Only split if the LEFT segment also has intent/structure, not just a bare
                 # product noun phrase. This prevents "Sodium Hydroxide and Soda Ash" from
                 # being split when "Soda Ash" is followed by a BUY keyword like "exporters".
                 left_lower = current_segment.strip().lower()
                 left_has_complexity = (
                     self._detect_intent_score(left_lower)[0] != 'AMBIGUOUS'
                     or any(kw in left_lower for kw in self.FAM_6_KEYWORDS + self.FAM_7_KEYWORDS + self.FAM_8_KEYWORDS)
                 )

                 if has_structural_intent or (has_intent and left_has_complexity):
                     final_segments.append(current_segment)
                     current_segment = part
                 else:
                     # Merge — right side has intent keywords but left is just a product name;
                     # treat the whole phrase as one query (e.g. "Caustic Soda exporters from India")
                     current_segment += " and " + part
             
             final_segments.append(current_segment)
             candidates = final_segments

        if len(candidates) > 1:
            sub_intents = []
            distinct_intents = set()
            
            for sq in candidates:
                if not sq.strip():
                    continue
                parsed = self._parse_single(sq, explicit_scope)
                sub_intents.append(parsed)
                distinct_intents.add(parsed['intent'])

            # Only return multi-intent if we found valid sub-intents
            # And if they are actually distinct logic, or just listing?
            # If all are same intent and product, maybe just merged filters?
            # But requirement says "Multi-intent".
            if len(sub_intents) > 1:
                # Only expose fields that belong to the top-level envelope.
                # Do NOT spread sub_intents[0] onto the top level — that leaks
                # the first sub-intent's country_filter / volume_mt / price_ceiling
                # into parsed_query, polluting any code that reads active_params
                # on the multi-intent branch.
                return {
                    "intent": sub_intents[0]['intent'],
                    "family": 9,
                    "product": sub_intents[0]['product'],
                    "scope": sub_intents[0].get('scope', 'WORLDWIDE'),
                    "multi_intent": True,
                    "sub_intents": sub_intents,
                    # Neutral top-level filter values — per-sub-intent filters live
                    # inside sub_intents[*] and are consumed by _run_sub_intent.
                    "country_filter": [],
                    "volume_mt": None,
                    "price_ceiling": None,
                    "price_floor": None,
                    "time_range": None,
                    "counterparty_name": None,
                }
        
        # Single intent path
        result = self._parse_single(query, explicit_scope)
        result["multi_intent"] = False

        # --- Phase 3-D: SetFit intent classifier ---
        # Overrides regex-derived intent/family when classifier confidence >= 0.70.
        result['classifier_confidence'] = 0.0
        if _USE_SETFIT:
            try:
                from search.services.setfit_classifier import (
                    get_setfit_classifier, SETFIT_TO_FAMILY, CONFIDENCE_THRESHOLD
                )
                clf = get_setfit_classifier()
                if clf.is_ready():
                    sf_label, sf_conf = clf.predict(query)
                    result['classifier_confidence'] = sf_conf
                    if sf_conf >= CONFIDENCE_THRESHOLD and sf_label in SETFIT_TO_FAMILY:
                        sf_intent, sf_family = SETFIT_TO_FAMILY[sf_label]
                        # For filter-only classes (F3–F8), preserve regex intent when
                        # it confidently detected SELL — SetFit only classifies the
                        # *structure* of these queries, not the buy/sell direction.
                        if sf_label not in ('BUY', 'SELL') and result.get('intent') == 'SELL':
                            sf_intent = 'SELL'
                        result['intent'] = sf_intent
                        result['family'] = sf_family
            except Exception:
                pass  # SetFit failure must never break the pipeline

        return result

    def _detect_intent_score(self, text):
        raw = text.lower()
        buy_score = 0
        sell_score = 0
        
        # Contextual Scoring
        for phrase, score in self.BUY_SCORES.items():
            if re.search(r'\b' + re.escape(phrase) + r'\b', raw):
                buy_score += score
        
        for phrase, score in self.SELL_SCORES.items():
            if re.search(r'\b' + re.escape(phrase) + r'\b', raw):
                sell_score += score
                
        # Heuristics for "from" / "to"
        # "buy from exporter" -> "buy from" (+5 BUY), "exporter" (+1 SELL) => BUY wins (5 > 1).
        # "sell to importer" -> "sell to" (+5 SELL), "importer" (+1 BUY) => SELL wins.
        
        if buy_score > sell_score:
            return 'BUY', buy_score
        elif sell_score > buy_score:
            return 'SELL', sell_score
        else:
            return 'AMBIGUOUS', 0

    def _parse_single(self, query, explicit_scope=None):
        """
        Parses a single atomic query segment.
        """
        raw_query = query.lower().strip()
        
        # Normalize explicit scope if provided
        scope = "WORLDWIDE"  # Default
        if explicit_scope and explicit_scope.upper() in ['PAKISTAN', 'WORLDWIDE']:
            scope = explicit_scope.upper()
            
        attributes = {
            "intent": None,
            "scope": scope,
            "family": 1, 
            "product": None,
            "volume_mt": None,
            "price_ceiling": None,
            "price_floor": None,
            "time_range": None,
            "country_filter": [],
            "counterparty_name": None
        }

        remainder = raw_query

        # --- 1. Identify Family Keywords ---
        is_rec = any(x in raw_query for x in self.FAM_6_KEYWORDS)
        is_mkt = any(x in raw_query for x in self.FAM_7_KEYWORDS)
        is_evid = (
            any(x in raw_query for x in self.FAM_8_KEYWORDS)
            # "Has [NAME] purchased/bought [product]" — name can be 1-5 words
            or bool(re.search(r'\bhas\s+\S+(?:\s+\S+){0,4}\s+(?:purchased|bought)\b', raw_query))
            # "Does [NAME] buy/purchase [product]"
            or bool(re.search(r'\bdoes\s+\S+(?:\s+\S+){0,4}\s+(?:buy|purchase|import)\b', raw_query))
        )

        # --- 2. Country Extraction (Fuzzy & Alias) ---
        found_countries = []
        
        # Check Aliases First
        # Sort aliases by length desc to match "United States of America" before "America"
        sorted_aliases = sorted(self.COUNTRY_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
             real_name = self.COUNTRY_ALIASES[alias]
             # Use negative lookahead (?!\w) instead of \b — \b doesn't match after '.'
             # for aliases like 'u.s.' at end of string or before space.
             esc_alias = re.escape(alias)
             pattern = r'\b' + esc_alias + r'(?!\w)'
             
             if re.search(pattern, remainder):
                 if real_name not in found_countries:
                     found_countries.append(real_name)
                 remainder = re.sub(pattern, '', remainder)

        # Check Standard List (loaded from DB, falls back to hardcoded list)
        _countries = self._get_countries()
        for country in _countries:
            pattern = r'\b' + re.escape(country.lower()) + r'\b'
            if re.search(pattern, remainder):
                if country not in found_countries:
                    found_countries.append(country)
                remainder = re.sub(pattern, '', remainder)

        # Fuzzy Match — catches typos like "Chna", "Germny", "Indonsia"
        tokens = remainder.split()
        for token in tokens:
            if len(token) < 4: continue
            # Remove dots/punctuation from token for fuzzy match
            clean_token = re.sub(r'[^\w]', '', token)
            # Short tokens (≤4 chars) are likely abbreviations like UAE, USA, KSA —
            # try uppercase first (most country lists store abbreviations in uppercase).
            lookup = clean_token.upper() if len(clean_token) <= 4 else clean_token.title()
            matches = difflib.get_close_matches(lookup, _countries, n=1, cutoff=0.85)
            if matches:
                c = matches[0]
                if c not in found_countries:
                    found_countries.append(c)
                    remainder = remainder.replace(token, '')

        attributes['country_filter'] = list(set(found_countries))

        # ... (Volume, Price, Time omitted for brevity, logic unchanged) ...
        # --- 3. Volume Extraction ---
        # Order matters: longer patterns first so "metric ton" / "metric tons" is captured
        # before the bare "ton" / "tons" alternative.
        vol_pattern = (
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*'
            r'(metric\s+tons?|mt|tonnes?|tons?|ton|kgs?|kilograms?|kilo)'
        )
        # Use case-insensitive search to catch "100MT"
        vol_match = re.search(vol_pattern, remainder, flags=re.IGNORECASE)
        if vol_match:
            qty_str = vol_match.group(1).replace(',', '')
            unit = vol_match.group(2).lower().strip()
            try:
                qty = float(qty_str)
                if re.match(r'^kilo', unit) or unit in ('kg', 'kgs', 'kilogram', 'kilograms'):
                    qty = qty / 1000.0
                attributes['volume_mt'] = qty
                remainder = remainder.replace(vol_match.group(0), '')
            except ValueError:
                pass

        # --- 4. Price Extraction (Enhanced) ---
        currency_regex = r'(?:\$|usd|eur|pkr|gbp|cny|rmb)'
        
        ceil_pattern = r'(?:under|below|<|cheaper th[ae]n|less th[ae]n|paying less th[ae]n)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)' + r'\s*' + currency_regex + r'?'
        ceil_match = re.search(ceil_pattern, remainder)
        if ceil_match:
            nums = re.findall(r'(\d+(?:,\d+)?)', ceil_match.group(0))
            if nums:
                raw = float(nums[0].replace(',', ''))
                attributes['price_ceiling'] = self._convert_to_usd(raw, ceil_match.group(0))
                remainder = remainder.replace(ceil_match.group(0), '')

        floor_pattern = r'(?:above|over|>|higher th[ae]n|more th[ae]n|greater th[ae]n|paying more th[ae]n|sell above|exceeding|at least)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)' + r'\s*' + currency_regex + r'?'
        floor_match = re.search(floor_pattern, remainder)
        if floor_match:
             nums = re.findall(r'(\d+(?:,\d+)?)', floor_match.group(0))
             if nums:
                raw = float(nums[0].replace(',', ''))
                attributes['price_floor'] = self._convert_to_usd(raw, floor_match.group(0))
                remainder = remainder.replace(floor_match.group(0), '')

        exact_pattern = r'\b(\d+(?:,\d+)?)\s*' + currency_regex + r'\b'
        exact_match = re.search(exact_pattern, remainder)
        if exact_match and not attributes['price_ceiling'] and not attributes['price_floor']:
             raw = float(exact_match.group(1).replace(',', ''))
             attributes['price_ceiling'] = self._convert_to_usd(raw, exact_match.group(0))
             remainder = remainder.replace(exact_match.group(0), '')

        # --- 5. Time Extraction (Enhanced) ---
        _MONTHS = (
            'january|february|march|april|may|june|july|august|september|'
            'october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec'
        )

        q_match = re.search(r'\b(q[1-4])[\s-]*(\d{4})?\b', remainder)
        if q_match:
            year = q_match.group(2) or str(datetime.date.today().year)
            attributes['time_range'] = f"{q_match.group(1).upper()} {year}"
            remainder = remainder.replace(q_match.group(0), '')

        if not attributes['time_range']:
            range_match = re.search(r'from\s+(\w+)\s+to\s+(\w+)', remainder)
            if range_match:
                attributes['time_range'] = f"{range_match.group(1)} to {range_match.group(2)}"
                remainder = remainder.replace(range_match.group(0), '')

        # "last N months/years"
        if not attributes['time_range']:
            time_pattern = r'last\s+(\d+)\s+((?:month|year)s?)'
            time_match = re.search(time_pattern, remainder)
            if time_match:
                attributes['time_range'] = f"last {time_match.group(1)} {time_match.group(2)}"
                remainder = remainder.replace(time_match.group(0), '')

        # "last year" / "last month"
        if not attributes['time_range']:
            m = re.search(r'\blast\s+(year|month)\b', remainder, re.IGNORECASE)
            if m:
                attributes['time_range'] = f"last 1 {m.group(1)}"
                remainder = remainder.replace(m.group(0), '')

        # "since <month>" or "since <month> <year>"
        if not attributes['time_range']:
            m = re.search(
                r'\bsince\s+(' + _MONTHS + r')(?:\s+(\d{4}))?\b',
                remainder, re.IGNORECASE
            )
            if m:
                month_str = m.group(1)
                year_str = m.group(len(m.groups())) or ''
                attributes['time_range'] = f"since {month_str} {year_str}".strip()
                remainder = remainder.replace(m.group(0), '')

        # "in <month> <year>" or "<month> <year>"
        if not attributes['time_range']:
            m = re.search(
                r'\b(?:in\s+)?(' + _MONTHS + r')\s+(\d{4})\b',
                remainder, re.IGNORECASE
            )
            if m:
                attributes['time_range'] = f"{m.group(1)} {m.group(2)}"
                remainder = remainder.replace(m.group(0), '')

        # Bare year e.g. "2023", "2024" — must be 4-digit year between 2000-2030
        if not attributes['time_range']:
            m = re.search(r'\b(20[0-3]\d)\b', remainder)
            if m:
                attributes['time_range'] = m.group(1)
                remainder = remainder.replace(m.group(0), '')
        
        # --- 6. Intent Detection (Scoring) ---
        # Run on `remainder` (countries/volumes/prices/times already stripped) so
        # that extracted filter values don't accidentally contribute intent signals.
        intent, score = self._detect_intent_score(remainder)
        attributes['intent'] = intent if intent != 'AMBIGUOUS' else 'BUY'

        # --- 7. Product & Counterparty Extraction ---
        # Strategy:
        # 1. Clean intent/family/stopwords.
        # 2. Check remaining text structure.
        # Heuristic: Counterparty is often consistent with:
        # - "Company X" (Capitalized in original, but we have lower) -> Hard
        # - Look for "from X", "by X" in *original query* or structure?
        
        # Let's try a regex for "Company X" pattern if it exists in the raw string?
        # Or just:
        # If "company" word is present?
        # If "ltd", "inc", "co" is present?
        
        # Clean phrases first
        clean_text = remainder
        
        # 1. Remove "Top N" / "Best N" phrases specifically to avoid leaving numbers behind
        # This fixes "Top 3 dextrose" -> "dextrose" (instead of "3 dextrose")
        clean_text = re.sub(r'\b(?:top|best|first|suggest|rank)\s+\d+\b', '', clean_text, flags=re.IGNORECASE)
        
        # Merge FAM_7 multi-word phrases into this sorted list so that e.g.
        # "export destinations" (18 chars) is removed before the single word
        # "export" (6 chars) can fragment it.
        fam7_multiword = [w for w in self.FAM_7_KEYWORDS if ' ' in w]
        all_phrases = sorted(
            list(self.BUY_SCORES.keys()) + list(self.SELL_SCORES.keys()) + fam7_multiword,
            key=len, reverse=True
        )
        for phrase in all_phrases:
             clean_text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', clean_text)
        # Sort longest phrases first so multi-word FAM_7 phrases (e.g. "top country")
        # are removed before their constituent FAM_6 single words (e.g. "top").
        all_fam_keywords = sorted(
            self.FAM_6_KEYWORDS + self.FAM_7_KEYWORDS + self.FAM_8_KEYWORDS,
            key=len, reverse=True
        )
        for w in all_fam_keywords:
             clean_text = re.sub(r'\b' + re.escape(w) + r'\b', '', clean_text)
        
        # Stopwords
        STOPWORDS = [
            " in ", " with ", " for ", " of ", " from ", " to ", " between ",
            "please", "search", "find", "show", "me", "list",
            "details", "price", "prices", "active", "recent", "data", "who", "is", "are",
            "import", "export", "importing", "exporting",
            "&",  # "and" intentionally excluded: merged product phrases like
            # "Sodium Hydroxide and Soda Ash" must survive product extraction.
            "importers", "buyers", "buyer", "importer", "buying", "selling",
            "can", "i", "sell", "buy", "have", "looking", "please", "want", "need", "give", "get", "away",
            "pay", "pays", "paying", "payment",
            "more", "less", "than", "above", "below", "under", "over",
            # Family-7 residual noise
            "the", "a", "an", "country", "countries", "market", "markets",
            "has", "do", "does", "where", "buys", "by", "per",
            "demand", "globally",
            # Possessives / first-person ("sell our wheat" → product should be "wheat")
            "our", "my", "your", "their", "its", "we", "us", "they", "them",
            # Logistics/packaging terms — not product names
            "bulk", "cargo", "lot", "consignment", "batch",
        ]
        
        # Remove common conversational prefixes
        prefixes = [
             "can i sell", "can i buy", "i want to sell", "i want to buy", 
             "looking to sell", "looking to buy", "i have", "i need", "need buyers for"
        ]
        text_lower = clean_text.lower()
        for p in prefixes:
             if text_lower.startswith(p):
                 clean_text = re.sub(r'^' + re.escape(p), '', clean_text, flags=re.IGNORECASE).strip()
        for sw in STOPWORDS:
            clean_text = re.sub(r'\b' + re.escape(sw.strip()) + r'\b', ' ', clean_text)
            
        clean_text = re.sub(r'[^\w\s\.]', '', clean_text).strip()
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Heuristic for "Company X sugar"
        # If "company" in text?
        if "company" in clean_text:
             # Split "company x" from "sugar"?
             # Assume "company x" comes first? or "sugar from company x"?
             # Difficult without specific separators.
             pass
             
        # Just use the whole clean text as product by default.
        attributes['product'] = clean_text
        
        # Specific fix for "Company X sugar"
        # If the user asks for "Company X sugar", implies they want to filter by supplier 'Company X' and product 'sugar'.
        # Without explicit "from", this is ambiguous.
        # BUT user feedback says: "Counterparty extraction is ignored -> Company X sugar becomes product..."
        # We need a way to extract it.
        # Check for known corporate suffixes in token? (Inc, Ltd, Co, Company)
        
        entity_match = re.search(r'\b(company \w+|[\w\s]+ (?:ltd|inc|co|corp))\b', clean_text)
        if entity_match:
            entity = entity_match.group(1)
            attributes['counterparty_name'] = entity.title()
            # Remove entity from product
            attributes['product'] = clean_text.replace(entity, '').strip()

        # Guard: remove countries that are embedded within a detected counterparty name.
        # e.g. "Nestle Pakistan Ltd" → counterparty_name set above, "Pakistan" must not
        # also appear in country_filter as a geo-filter. Mirrors the same guard in F8.
        if attributes.get('counterparty_name') and attributes['country_filter']:
            cp_lower = attributes['counterparty_name'].lower()
            attributes['country_filter'] = [
                c for c in attributes['country_filter']
                if c.lower() not in cp_lower
            ]

        # --- 9. Family Classification ---
        # ... (Same as before) ...
        f = 1
        if is_evid: f = 8
        elif is_mkt: f = 7
        elif is_rec: f = 6
        elif attributes['price_ceiling'] or attributes['price_floor']: f = 4
        elif attributes['volume_mt'] and attributes['time_range']: f = 3  # volume takes priority when both present; time_filter still applied in aggregation
        elif attributes['time_range']: f = 5
        elif attributes['volume_mt']: f = 3
        elif attributes['country_filter']: f = 2
        else: f = 1
        
        attributes['family'] = f

        # --- F8: Buyer name extraction (run on original-case query) ---
        # Always runs for F8 and overrides the generic entity_match result, which
        # can pick up noise words (e.g., "provide ... corp" → "Provide Corp").
        if f == 8:
            buyer_name_extracted = None

            # Pattern 1: "Has <BUYER> purchased/bought [product]"
            m = re.search(r'\bhas\s+(.+?)\s+(?:purchased|bought)\b', query, re.IGNORECASE)
            if m:
                buyer_name_extracted = m.group(1).strip()

            # Pattern 2: "shipments (from X) to <BUYER>"
            if not buyer_name_extracted:
                m = re.search(r'\bshipments\s+(?:\w+\s+\w+\s+)?to\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
                if m:
                    buyer_name_extracted = m.group(1).strip().rstrip('?').strip()

            # Pattern 3: "evidence/invoices/history/record/verify for <BUYER>"
            # Only matches if the name begins with an uppercase letter (proper noun / company name).
            # This prevents product names like "dextrose" from being misidentified as buyers.
            if not buyer_name_extracted:
                m = re.search(
                    r'\b(?:evidence|invoices?|history|record|verification|proof|verify)\s+(?:for|of|by)\s+([A-Z]\w[\w\s]*?)(?:\?|$)',
                    query  # original-case query — NOT re.IGNORECASE
                )
                if m:
                    buyer_name_extracted = m.group(1).strip().rstrip('?').strip()

            # Pattern 4: "does <BUYER> buy/purchase/import <product>"
            # Buyer name is everything between "does" and the verb.
            if not buyer_name_extracted:
                m = re.search(
                    r'\bdoes\s+(.+?)\s+(?:buy|purchase|import)\b',
                    query, re.IGNORECASE
                )
                if m:
                    buyer_name_extracted = m.group(1).strip()

            # Set (or clear if no F8 pattern matched) — override generic entity_match noise
            attributes['counterparty_name'] = buyer_name_extracted

            # Remove countries that are embedded within the buyer company name from country_filter.
            # e.g. "Pakistan" in "Nestle Pakistan Ltd" is part of the name, not a geo-filter.
            if buyer_name_extracted and attributes['country_filter']:
                buyer_lower = buyer_name_extracted.lower()
                attributes['country_filter'] = [
                    c for c in attributes['country_filter']
                    if c.lower() not in buyer_lower
                ]

            # Strip the buyer name from the extracted product to avoid contamination.
            # Try full phrase first; if not found, strip individual tokens (≥4 chars).
            if buyer_name_extracted and attributes['product']:
                cn_lower = buyer_name_extracted.lower()
                p = attributes['product']
                if cn_lower in p.lower():
                    p = re.sub(re.escape(cn_lower), '', p, flags=re.IGNORECASE)
                else:
                    for token in cn_lower.split():
                        if len(token) >= 4:
                            p = re.sub(r'\b' + re.escape(token) + r'\b', '', p, flags=re.IGNORECASE)
                attributes['product'] = re.sub(r'\s+', ' ', p).strip()

            # Strip F8-specific noise words from product (e.g., "purchased", "before", "deal")
            if attributes['product']:
                p = attributes['product']
                for noise in self.FAM_8_PRODUCT_NOISE:
                    p = re.sub(r'\b' + re.escape(noise) + r'\b', '', p, flags=re.IGNORECASE)
                attributes['product'] = re.sub(r'\s+', ' ', p).strip()

        # --- GLiNER NER: fill gaps from regex extraction ---
        # Runs after all regex steps; only fills fields that regex left as None.
        attributes['ner_confidence'] = 1.0
        attributes['ambiguous_query'] = False
        if _USE_GLINER:
            try:
                from search.services.ner_extractor import get_ner_extractor
                extractor = get_ner_extractor()
                gliner_result = extractor.extract(query)

                # Build regex_result aligned with GLiNER field names
                # Regex takes precedence; GLiNER fills gaps.
                # Exception: if the regex product starts with a quantity word (e.g. "fifty
                # metric tons dextrose ..."), pass None so GLiNER can clean it up.
                _QUANTITY_WORDS_SET = {'zero','one','two','three','four','five','six','seven',
                                       'eight','nine','ten','twenty','thirty','forty','fifty',
                                       'sixty','seventy','eighty','ninety','hundred','thousand',
                                       'million','dozen','metric','tons','ton','mt','kg','kgs'}
                _raw_prod = attributes.get('product') or None
                _prod_is_qty_polluted = bool(
                    _raw_prod and _raw_prod.lower().split()[0] in _QUANTITY_WORDS_SET
                )
                regex_aligned = {
                    'product':             None if _prod_is_qty_polluted else _raw_prod,
                    'quantity':            attributes.get('volume_mt'),
                    'unit':                None,  # unit was already applied to volume_mt
                    'origin_country':      attributes['country_filter'][0] if attributes['country_filter'] else None,
                    'destination_country': None,
                    'price_ceiling':       attributes.get('price_ceiling'),
                    'price_floor':         attributes.get('price_floor'),
                    'hs_code':             None,
                    'company_name':        attributes.get('counterparty_name'),
                    'time_period':         attributes.get('time_range'),
                }
                merged = extractor.merge_with_regex(gliner_result, regex_aligned)

                # Apply merged values back to attributes (fill gaps only)
                if (not attributes.get('product') or _prod_is_qty_polluted) and merged.get('product'):
                    attributes['product'] = merged['product']

                if attributes.get('volume_mt') is None and merged.get('quantity'):
                    qty = merged['quantity']
                    # Convert to MT if unit is KG
                    if merged.get('unit') == 'KG':
                        qty = qty / 1000.0
                    attributes['volume_mt'] = qty

                if not attributes['country_filter'] and merged.get('origin_country'):
                    _gliner_country = merged['origin_country']
                    # Validate: only accept if it's a known country name, not a generic word
                    _countries = self._get_countries()
                    _known = set(c.lower() for c in _countries) | set(self.COUNTRY_ALIASES.values())
                    if _gliner_country.lower() in _known or _gliner_country in _countries:
                        attributes['country_filter'] = [_gliner_country]

                if attributes.get('price_ceiling') is None and merged.get('price_ceiling'):
                    attributes['price_ceiling'] = merged['price_ceiling']

                if attributes.get('price_floor') is None and merged.get('price_floor'):
                    attributes['price_floor'] = merged['price_floor']

                if not attributes.get('counterparty_name') and merged.get('company_name'):
                    attributes['counterparty_name'] = merged['company_name']

                if not attributes.get('time_range') and merged.get('time_period'):
                    attributes['time_range'] = merged['time_period']

                attributes['ner_confidence'] = gliner_result.get('ner_confidence', 1.0)
                if attributes['ner_confidence'] < 0.40:
                    attributes['ambiguous_query'] = True
            except Exception:
                pass  # GLiNER failure must never break the pipeline

        # Guard: if family=7 was triggered solely by ambiguous non-country keywords
        # (compare, vs, cheapest, lowest price) and fewer than 2 countries were extracted,
        # it is a product/price comparison, not a country comparison — downgrade.
        # A single country is not a comparison (e.g. "cheapest dextrose from China" → Family 2/4).
        if f == 7 and len(attributes['country_filter']) <= 1:
            AMBIGUOUS_F7 = {'cheapest', 'lowest price', 'compare', 'vs'}
            triggered = [kw for kw in self.FAM_7_KEYWORDS if kw in raw_query]
            # Don't downgrade if query explicitly mentions "countr" (country/countries)
            query_has_country_word = bool(re.search(r'\bcountr', raw_query))
            if triggered and all(kw in AMBIGUOUS_F7 for kw in triggered) and not query_has_country_word:
                if attributes['price_ceiling'] or attributes['price_floor']:
                    f = 4
                elif attributes['country_filter']:
                    f = 2
                else:
                    f = 1
                attributes['family'] = f

        # Family 7 intent override:
        # Phrases like "which country buys", "by country", "buyers by country" clearly
        # ask for BUYER markets — i.e. the user is a SELLER looking for destinations.
        # Without this override, the word "buy/buys" would push intent to BUY incorrectly.
        if f == 7 and attributes['intent'] == 'BUY':
            BUYER_MARKET_PHRASES = [
                'which country', 'which countries', 'by country', 'per country',
                'buyers by country', 'country breakdown', 'breakdown by country',
                'highest demand', 'most demand', 'where is demand', 'where is highest',
                'best market', 'best country', 'top market', 'top country',
                'export destinations',
            ]
            if any(phrase in raw_query for phrase in BUYER_MARKET_PHRASES):
                attributes['intent'] = 'SELL'

        return attributes
