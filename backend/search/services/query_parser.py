import re
import math
import difflib

class QueryInterpreter:
    """Parses NL queries into structured intent and attributes (no DB lookups)."""

    COUNTRIES = [
        "Pakistan", "China", "India", "Brazil", "USA", "United States", "UAE", "Dubai",
        "Vietnam", "Thailand", "Indonesia", "Germany", "France", "UK", "United Kingdom",
        "Russia", "Turkey", "Egypt", "Saudi Arabia", "Canada", "Australia", "Malaysia",
        "Kenya", "Bangladesh", "Sri Lanka", "Japan", "Korea", "South Korea", "Afghanistan"
    ]
    
    COUNTRY_ALIASES = {
        "us": "USA", "u.s.": "USA", "united states of america": "USA", "america": "USA",
        "uae": "UAE", "u.a.e": "UAE", "emirates": "UAE",
        "uk": "UK", "u.k.": "UK", "britain": "UK",
        "ksa": "Saudi Arabia"
    }

    BUY_SCORES = {
        "who sells": 5, "suppliers of": 5, "supplier": 3, "find exporters": 5, "find suppliers": 5,
        "source from": 5, "buy from": 5, "i want to buy": 5, "buying": 3, "imports": 2,
        "want to import": 4, "buy": 1, "purchase": 2, "sourcing": 3, "need": 2, "importers": 1,
        "suppliers": 3
    }
    
    SELL_SCORES = {
        "who buys": 5, "buyers for": 5, "buyer": 3, "find importers": 5, "find buyers": 5,
        "demand for": 5, "sell to": 5, "i want to sell": 5, "selling": 3, "exports": 2,
        "want to export": 4, "sell": 1, "supply": 2, "available": 2, "exporters": 1,
        "demands": 3,
        "buyers": 3, "pay": 3, "pays": 3, "paying": 3, "who pay": 5,
        "looking to sell": 5, "i have": 5, "can i sell": 5
    }

    FAM_6_KEYWORDS = ["top", "best", "rank", "suggest", "recommend", "highest", "most", "paying"]
    FAM_7_KEYWORDS = ["cheapest", "lowest price", "highest demand", "compare", "vs"]
    FAM_8_KEYWORDS = ["shipments", "transactions", "history", "record", "proof", "verification", "evidence"]

    def parse(self, query, explicit_scope=None):
        """explicit_scope overrides any inferred scope (e.g. set by frontend)."""
        if not query:
            return {}

        # Split by ';' always; split by 'and' only when the right side has its
        # own intent keyword. Otherwise "rice and wheat" wrongly fragments.
        candidates = re.split(r';', query)
        if len(candidates) == 1:
             parts = re.split(r'\b(?:and|also)\b', query, flags=re.IGNORECASE)
             final_segments = []
             current_segment = parts[0]

             for part in parts[1:]:
                 has_intent = self._detect_intent_score(part)[0] != 'AMBIGUOUS'

                 if has_intent:
                     final_segments.append(current_segment)
                     current_segment = part
                 else:
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

            if len(sub_intents) > 1:
                 return {
                     "intent": sub_intents[0]['intent'],
                     "family": 9,
                     "product": sub_intents[0]['product'],
                     "multi_intent": True,
                     "sub_intents": sub_intents,
                     **{k:v for k,v in sub_intents[0].items() if k not in ['intent', 'family', 'product']}
                 }

        result = self._parse_single(query, explicit_scope)
        result["multi_intent"] = False
        return result

    def _detect_intent_score(self, text):
        raw = text.lower()
        buy_score = 0
        sell_score = 0

        for phrase, score in self.BUY_SCORES.items():
            if re.search(r'\b' + re.escape(phrase) + r'\b', raw):
                buy_score += score

        for phrase, score in self.SELL_SCORES.items():
            if re.search(r'\b' + re.escape(phrase) + r'\b', raw):
                sell_score += score

        if buy_score > sell_score:
            return 'BUY', buy_score
        elif sell_score > buy_score:
            return 'SELL', sell_score
        else:
            return 'AMBIGUOUS', 0

    def _parse_single(self, query, explicit_scope=None):
        raw_query = query.lower().strip()

        scope = "WORLDWIDE"
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

        is_rec = any(x in raw_query for x in self.FAM_6_KEYWORDS)
        is_mkt = any(x in raw_query for x in self.FAM_7_KEYWORDS)
        is_evid = any(x in raw_query for x in self.FAM_8_KEYWORDS)

        found_countries = []

        # Sort aliases longest-first so 'united states of america' matches before 'america'.
        sorted_aliases = sorted(self.COUNTRY_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
             real_name = self.COUNTRY_ALIASES[alias]
             # Negative-lookahead (?!\w) instead of \b — \b fails after '.' in 'u.s.'
             esc_alias = re.escape(alias)
             pattern = r'\b' + esc_alias + r'(?!\w)'

             if re.search(pattern, remainder):
                 if real_name not in found_countries:
                     found_countries.append(real_name)
                 remainder = re.sub(pattern, '', remainder)

        for country in self.COUNTRIES:
            pattern = r'\b' + re.escape(country.lower()) + r'\b'
            if re.search(pattern, remainder):
                if country not in found_countries:
                    found_countries.append(country)
                remainder = re.sub(pattern, '', remainder)

        tokens = remainder.split()
        for token in tokens:
            if len(token) < 4: continue
            clean_token = re.sub(r'[^\w]', '', token)
            matches = difflib.get_close_matches(clean_token.title(), self.COUNTRIES, n=1, cutoff=0.85)
            if matches:
                c = matches[0]
                if c not in found_countries:
                    found_countries.append(c)
                    remainder = remainder.replace(token, '')

        attributes['country_filter'] = list(set(found_countries))

        vol_pattern = r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(mt|tons|metric tons|kg|kilo|tonnes)'
        vol_match = re.search(vol_pattern, remainder, flags=re.IGNORECASE)
        if vol_match:
            qty_str = vol_match.group(1).replace(',', '')
            unit = vol_match.group(2)
            try:
                qty = float(qty_str)
                if unit in ['kg', 'kilo']:
                    qty = qty / 1000.0
                attributes['volume_mt'] = qty
                remainder = remainder.replace(vol_match.group(0), '')
            except ValueError:
                pass

        currency_regex = r'(?:\$|usd|eur|pkr|gbp|cny|rmb)'
        
        ceil_pattern = r'(?:under|below|<|cheaper than|less than|paying less than)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)' + r'\s*' + currency_regex + r'?'
        ceil_match = re.search(ceil_pattern, remainder)
        if ceil_match:
            nums = re.findall(r'(\d+(?:,\d+)?)', ceil_match.group(0))
            if nums:
                attributes['price_ceiling'] = float(nums[0].replace(',', ''))
                remainder = remainder.replace(ceil_match.group(0), '')

        floor_pattern = r'(?:above|over|>|higher than|more than|paying more than|sell above)\s*' + currency_regex + r'?\s*(\d+(?:,\d+)?)' + r'\s*' + currency_regex + r'?'
        floor_match = re.search(floor_pattern, remainder)
        if floor_match:
             nums = re.findall(r'(\d+(?:,\d+)?)', floor_match.group(0))
             if nums:
                attributes['price_floor'] = float(nums[0].replace(',', ''))
                remainder = remainder.replace(floor_match.group(0), '')

        exact_pattern = r'\b(\d+(?:,\d+)?)\s*' + currency_regex + r'\b'
        exact_match = re.search(exact_pattern, remainder)
        if exact_match and not attributes['price_ceiling'] and not attributes['price_floor']:
             attributes['price_ceiling'] = float(exact_match.group(1).replace(',', ''))
             remainder = remainder.replace(exact_match.group(0), '')

        q_match = re.search(r'\b(q[1-4])[\s-]*(\d{4})?\b', remainder)
        if q_match:
            year = q_match.group(2) or "2025"
            attributes['time_range'] = f"{q_match.group(1).upper()} {year}"
            remainder = remainder.replace(q_match.group(0), '')

        range_match = re.search(r'from\s+(\w+)\s+to\s+(\w+)', remainder)
        if range_match:
             attributes['time_range'] = f"{range_match.group(1)} to {range_match.group(2)}"
             remainder = remainder.replace(range_match.group(0), '')

        time_pattern = r'last\s+(\d+)\s+((?:month|year)s?)'
        time_match = re.search(time_pattern, remainder)
        if time_match:
            attributes['time_range'] = f"last {time_match.group(1)} {time_match.group(2)}"
            remainder = remainder.replace(time_match.group(0), '')
        
        intent, score = self._detect_intent_score(query)
        attributes['intent'] = intent if intent != 'AMBIGUOUS' else 'BUY'

        clean_text = remainder

        # Strip "Top 3 dextrose" -> "dextrose" first so the number doesn't leak.
        clean_text = re.sub(r'\b(?:top|best|first|suggest|rank)\s+\d+\b', '', clean_text, flags=re.IGNORECASE)
        
        all_phrases = sorted(list(self.BUY_SCORES.keys()) + list(self.SELL_SCORES.keys()), key=len, reverse=True)
        for phrase in all_phrases:
             clean_text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', clean_text)
        for w in self.FAM_6_KEYWORDS + self.FAM_7_KEYWORDS + self.FAM_8_KEYWORDS:
             clean_text = re.sub(r'\b' + re.escape(w) + r'\b', '', clean_text)

        STOPWORDS = [
            " in ", " with ", " for ", " of ", " from ", " to ", " between ",
            "please", "search", "find", "show", "me", "list", 
            "details", "price", "prices", "active", "recent", "data", "who", "is", "are",
            "import", "export", "importing", "exporting",
            "and", "&",
            "importers", "buyers", "buyer", "importer", "buying", "selling",
            "can", "i", "sell", "buy", "have", "looking", "please", "want", "need", "give", "get",
            "pay", "pays", "paying", "payment",
            "more", "less", "than", "above", "below", "under", "over"
        ]

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

        if "company" in clean_text:
             pass

        attributes['product'] = clean_text

        # Detect entity (e.g. "Company X" / "X Ltd") to separate counterparty from product.
        entity_match = re.search(r'\b(company \w+|[\w\s]+ (?:ltd|inc|co|corp))\b', clean_text)
        if entity_match:
            entity = entity_match.group(1)
            attributes['counterparty_name'] = entity.title()
            attributes['product'] = clean_text.replace(entity, '').strip()

        f = 1
        if is_evid: f = 8
        elif is_mkt: f = 7
        elif is_rec: f = 6
        elif attributes['price_ceiling'] or attributes['price_floor']: f = 4
        elif attributes['time_range']: f = 5
        elif attributes['volume_mt']: f = 3
        elif attributes['country_filter']: f = 2
        else: f = 1

        attributes['family'] = f

        return attributes
