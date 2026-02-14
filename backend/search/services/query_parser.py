import re
import math
import difflib

class QueryInterpreter:
    """
    Parses natural language queries into structured intent and attributes.
    Does NOT perform retrieval or database lookups.
    """

    # Common trading countries (expand as needed or load from DB)
    COUNTRIES = [
        "Pakistan", "China", "India", "Brazil", "USA", "United States", "UAE", "Dubai",
        "Vietnam", "Thailand", "Indonesia", "Germany", "France", "UK", "United Kingdom",
        "Russia", "Turkey", "Egypt", "Saudi Arabia", "Canada", "Australia", "Malaysia",
        "Kenya", "Bangladesh", "Sri Lanka", "Japan", "Korea", "South Korea"
    ]
    
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
        "want to import": 4, "buy": 1, "purchase": 2, "sourcing": 3, "need": 2, "importers": 1,
        "suppliers": 3
    }
    
    SELL_SCORES = {
        "who buys": 5, "buyers for": 5, "buyer": 3, "find importers": 5, "find buyers": 5,
        "demand for": 5, "sell to": 5, "i want to sell": 5, "selling": 3, "exports": 2,
        "want to export": 4, "sell": 1, "supply": 2, "available": 2, "exporters": 1,
        "demands": 3,
        "buyers": 3
    }

    # Family Parsing Keywords
    FAM_6_KEYWORDS = ["top", "best", "rank", "suggest", "recommend"]
    FAM_7_KEYWORDS = ["cheapest", "lowest price", "highest demand", "compare", "vs"]
    FAM_8_KEYWORDS = ["shipments", "transactions", "history", "record", "proof", "verification", "evidence"]

    def parse(self, query, explicit_scope=None):
        """
        Main entry point. Handles multi-intent splitting.
        explicit_scope: If provided (e.g., from frontend), overrides any scope inference.
        """
        if not query:
            return {}

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
                 
                 # 2. Or has Country AND Product structure? (Heuristic)
                 # If it's just a country "China", do NOT split.
                 # If "China and India", 'India' has no intent, likely just country.
                 
                 if has_intent:
                     final_segments.append(current_segment)
                     current_segment = part
                 else:
                     # Merge
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
                 return {
                     "intent": sub_intents[0]['intent'], 
                     "family": 9,
                     "product": sub_intents[0]['product'],
                     "multi_intent": True,
                     "sub_intents": sub_intents,
                     **{k:v for k,v in sub_intents[0].items() if k not in ['intent', 'family', 'product']}
                 }
        
        # Single intent path
        result = self._parse_single(query, explicit_scope)
        result["multi_intent"] = False
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
        is_evid = any(x in raw_query for x in self.FAM_8_KEYWORDS)

        # --- 2. Country Extraction (Fuzzy & Alias) ---
        found_countries = []
        
        # Check Aliases First
        # Sort aliases by length desc to match "United States of America" before "America"
        sorted_aliases = sorted(self.COUNTRY_ALIASES.keys(), key=len, reverse=True)
        for alias in sorted_aliases:
             real_name = self.COUNTRY_ALIASES[alias]
             # Update regex to handle dots properly (escape dots in alias)
             # And ensure boundary or end of string
             esc_alias = re.escape(alias)
             pattern = r'\b' + esc_alias + r'\b'
             
             # Problem: \b doesn't match after '.' if alias ends with '.' like 'u.s.'
             # Fix: Use negative lookahead (?!\w) which ensures next char is NOT a word char.
             # This works for "u.s." at end of string or before space.
             
             esc_alias = re.escape(alias)
             pattern = r'\b' + esc_alias + r'(?!\w)'
             
             if re.search(pattern, remainder):
                 if real_name not in found_countries:
                     found_countries.append(real_name)
                 remainder = re.sub(pattern, '', remainder)

        # Check Standard List
        for country in self.COUNTRIES:
            pattern = r'\b' + re.escape(country.lower()) + r'\b'
            if re.search(pattern, remainder):
                if country not in found_countries:
                    found_countries.append(country) 
                remainder = re.sub(pattern, '', remainder)

        # Fuzzy Match
        tokens = remainder.split()
        for token in tokens:
            if len(token) < 4: continue
            # Remove dots/punctuation from token for fuzzy match
            clean_token = re.sub(r'[^\w]', '', token)
            matches = difflib.get_close_matches(clean_token.title(), self.COUNTRIES, n=1, cutoff=0.85)
            if matches:
                c = matches[0]
                if c not in found_countries:
                    found_countries.append(c)
                    remainder = remainder.replace(token, '')

        attributes['country_filter'] = list(set(found_countries))

        # ... (Volume, Price, Time omitted for brevity, logic unchanged) ...
        # --- 3. Volume Extraction ---
        vol_pattern = r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(mt|tons|metric tons|kg|kilo|tonnes)'
        # Use case-insensitive search to catch "100MT"
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

        # --- 4. Price Extraction (Enhanced) ---
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

        # --- 5. Time Extraction (Enhanced) ---
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
        
        # --- 6. Intent Detection (Scoring) ---
        intent, score = self._detect_intent_score(query) 
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
        
        all_phrases = sorted(list(self.BUY_SCORES.keys()) + list(self.SELL_SCORES.keys()), key=len, reverse=True)
        for phrase in all_phrases:
             clean_text = re.sub(r'\b' + re.escape(phrase) + r'\b', '', clean_text)
        for w in self.FAM_6_KEYWORDS + self.FAM_7_KEYWORDS + self.FAM_8_KEYWORDS:
             clean_text = re.sub(r'\b' + re.escape(w) + r'\b', '', clean_text)
        
        # Stopwords
        STOPWORDS = [
            " in ", " with ", " for ", " of ", " from ", " to ", " between ",
            "please", "search", "find", "show", "me", "list", 
            "details", "price", "prices", "active", "recent", "data", "who", "is", "are",
            "import", "export", "importing", "exporting",
            "and", "&",
            "importers", "buyers", "buyer", "importer", "buying", "selling"
        ]
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
            
        # --- 9. Family Classification ---
        # ... (Same as before) ...
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
