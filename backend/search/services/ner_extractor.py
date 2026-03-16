"""
backend/search/services/ner_extractor.py

GLiNER-based zero-shot NER for trade query parsing.

Model: urchade/gliner_medium-v2.1
  - ~450 MB, ~30ms per query on CPU
  - Zero-shot: no fine-tuning needed, label names define entity types

Labels:
    product              - ingredient/commodity name ("dextrose anhydrous", "palm oil")
    quantity             - numeric amount ("50", "100")
    unit                 - measurement unit ("MT", "metric tons", "kg")
    origin_country       - country of origin ("China", "India", "Brazil")
    destination_country  - import destination ("Pakistan", etc.)
    price_ceiling        - upper price bound ("$400", "400 per MT")
    price_floor          - lower price bound ("above $300")
    hs_code              - harmonized system code ("1702.11", "17.02")
    company_name         - company / organization name ("Nestle", "Al Khaleej")
    time_period          - temporal reference ("Q1 2024", "last 6 months", "2023")

GLiNER fills gaps that regex misses (novel phrasing, ordinal numbers, etc.).
Regex results always take precedence when both sources produce a value.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------
GLINER_MODEL = 'urchade/gliner_medium-v2.1'

LABELS = [
    "product",
    "quantity",
    "unit",
    "origin_country",
    "destination_country",
    "price_ceiling",
    "price_floor",
    "hs_code",
    "company_name",
    "time_period",
]

# Canonical unit mapping
_UNIT_MAP = {
    'mt': 'MT', 'mts': 'MT', 'metric ton': 'MT', 'metric tons': 'MT',
    'tonne': 'MT', 'tonnes': 'MT', 'ton': 'MT', 'tons': 'MT',
    'kg': 'KG', 'kilogram': 'KG', 'kilograms': 'KG',
    'g': 'G', 'gram': 'G', 'grams': 'G',
    'lb': 'LB', 'lbs': 'LB', 'pound': 'LB', 'pounds': 'LB',
}

# Word-to-number for quantity normalization
_WORD_NUM = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'twenty': 20, 'thirty': 30, 'forty': 40,
    'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1000, 'million': 1_000_000,
}


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _to_float(text: str) -> Optional[float]:
    """Convert a string to float, handling commas and word numbers."""
    if not text:
        return None
    text = text.strip().replace(',', '').replace('$', '').lower()
    # Try direct parse
    try:
        return float(text)
    except ValueError:
        pass
    # Word number
    return _WORD_NUM.get(text)


def _canonical_unit(text: str) -> Optional[str]:
    return _UNIT_MAP.get(text.strip().lower())


def _strip_price_symbols(text: str) -> Optional[float]:
    """Extract float from strings like '$400', '400/MT', 'USD 350'."""
    cleaned = re.sub(r'[^\d.]', ' ', text).split()
    for token in cleaned:
        try:
            return float(token)
        except ValueError:
            continue
    return None


# -----------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------
_extractor_instance: Optional['GLiNERExtractor'] = None


def get_ner_extractor() -> 'GLiNERExtractor':
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = GLiNERExtractor()
    return _extractor_instance


# -----------------------------------------------------------------------
# GLiNERExtractor
# -----------------------------------------------------------------------

class GLiNERExtractor:
    """
    Extracts structured fields from trade queries using GLiNER zero-shot NER.

    Usage:
        extractor = GLiNERExtractor()
        result = extractor.extract("50 MT of dextrose from China under $400/MT")
        # {'product': 'dextrose', 'quantity': 50.0, 'unit': 'MT',
        #  'origin_country': 'China', 'price_ceiling': 400.0, ...}
    """

    _model = None   # class-level singleton
    _loaded = False

    def _load(self) -> bool:
        if self.__class__._loaded:
            return self.__class__._model is not None
        try:
            from gliner import GLiNER
            self.__class__._model = GLiNER.from_pretrained(GLINER_MODEL)
            self.__class__._loaded = True
            logger.info(f"GLiNER loaded: {GLINER_MODEL}")
            return True
        except Exception as e:
            self.__class__._loaded = True   # mark as attempted
            logger.warning(f"GLiNER load failed ({e}); NER will return empty dict")
            return False

    # ------------------------------------------------------------------

    def extract(self, query: str) -> dict:
        """
        Run GLiNER NER on a query and return a structured dict.

        Returns:
            {
                'product': str | None,
                'quantity': float | None,
                'unit': str | None,              # canonical: 'MT', 'KG', 'G', 'LB'
                'origin_country': str | None,
                'destination_country': str | None,
                'price_ceiling': float | None,
                'price_floor': float | None,
                'hs_code': str | None,
                'company_name': str | None,
                'time_period': str | None,
                'ner_confidence': float,          # min confidence across all non-None extractions
            }
        """
        empty = {k: None for k in [
            'product', 'quantity', 'unit', 'origin_country', 'destination_country',
            'price_ceiling', 'price_floor', 'hs_code', 'company_name', 'time_period',
        ]}
        empty['ner_confidence'] = 1.0

        if not self._load():
            return empty

        try:
            entities = self.__class__._model.predict_entities(query, LABELS, threshold=0.4)
        except Exception as e:
            logger.warning(f"GLiNER inference error: {e}")
            return empty

        return self._post_process(entities, empty)

    def _post_process(self, entities: list, result: dict) -> dict:
        """Convert raw GLiNER entities to clean field dict."""
        confidences = []

        for ent in entities:
            label = ent.get('label', '')
            text = ent.get('text', '').strip()
            score = float(ent.get('score', 1.0))
            confidences.append(score)

            if label == 'product' and result['product'] is None:
                result['product'] = text

            elif label == 'quantity' and result['quantity'] is None:
                result['quantity'] = _to_float(text)

            elif label == 'unit' and result['unit'] is None:
                result['unit'] = _canonical_unit(text) or text.upper()

            elif label == 'origin_country' and result['origin_country'] is None:
                result['origin_country'] = text.title()

            elif label == 'destination_country' and result['destination_country'] is None:
                result['destination_country'] = text.title()

            elif label == 'price_ceiling' and result['price_ceiling'] is None:
                result['price_ceiling'] = _strip_price_symbols(text)

            elif label == 'price_floor' and result['price_floor'] is None:
                result['price_floor'] = _strip_price_symbols(text)

            elif label == 'hs_code' and result['hs_code'] is None:
                result['hs_code'] = text

            elif label == 'company_name' and result['company_name'] is None:
                result['company_name'] = text

            elif label == 'time_period' and result['time_period'] is None:
                result['time_period'] = text

        result['ner_confidence'] = min(confidences) if confidences else 1.0
        return result

    # ------------------------------------------------------------------

    def merge_with_regex(self, gliner_result: dict, regex_result: dict) -> dict:
        """
        Merge GLiNER and regex extraction results.

        Precedence rules:
          - Regex takes precedence for all fields when it returns a non-None value.
          - GLiNER fills in any field that regex returned None for.
          - Disagreements (both non-None but different values) are logged at DEBUG.

        Returns merged dict with all keys from gliner_result plus any extra from regex_result.
        """
        merged = dict(gliner_result)

        for key, regex_val in regex_result.items():
            gliner_val = gliner_result.get(key)

            if regex_val is not None:
                # Regex takes precedence
                if gliner_val is not None and gliner_val != regex_val:
                    logger.debug(
                        "NER merge disagreement on '%s': gliner=%r regex=%r → using regex",
                        key, gliner_val, regex_val,
                    )
                merged[key] = regex_val
            elif gliner_val is not None:
                # GLiNER fills the gap
                merged[key] = gliner_val
            # else: both None — leave as None

        return merged
