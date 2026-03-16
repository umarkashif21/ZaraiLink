"""
Tests for GLiNER-based NER extractor (Phase 3-A/3-B).

Unit tests mock GLiNER model — no live model download required.
Integration tests load the real model (marked @pytest.mark.slow).
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(label, text, score=0.85):
    return {'label': label, 'text': text, 'score': score}


def _make_extractor_with_mock(entities):
    """Return a GLiNERExtractor whose GLiNER model returns `entities`."""
    from search.services.ner_extractor import GLiNERExtractor
    e = GLiNERExtractor()
    mock_model = MagicMock()
    mock_model.predict_entities.return_value = entities
    GLiNERExtractor._model = mock_model
    GLiNERExtractor._loaded = True
    return e


def _reset_singleton():
    from search.services import ner_extractor as m
    m._extractor_instance = None
    from search.services.ner_extractor import GLiNERExtractor
    GLiNERExtractor._model = None
    GLiNERExtractor._loaded = False


# ---------------------------------------------------------------------------
# Unit tests — _helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_to_float_numeric_string(self):
        from search.services.ner_extractor import _to_float
        assert _to_float('50') == 50.0
        assert _to_float('1,000') == 1000.0

    def test_to_float_word_fifty(self):
        from search.services.ner_extractor import _to_float
        assert _to_float('fifty') == 50.0

    def test_to_float_none_on_unknown(self):
        from search.services.ner_extractor import _to_float
        assert _to_float('unknown') is None

    def test_canonical_unit_mt(self):
        from search.services.ner_extractor import _canonical_unit
        assert _canonical_unit('metric tons') == 'MT'
        assert _canonical_unit('MT') == 'MT'
        assert _canonical_unit('tonnes') == 'MT'

    def test_canonical_unit_kg(self):
        from search.services.ner_extractor import _canonical_unit
        assert _canonical_unit('kg') == 'KG'
        assert _canonical_unit('kilograms') == 'KG'

    def test_strip_price_symbols(self):
        from search.services.ner_extractor import _strip_price_symbols
        assert _strip_price_symbols('$400') == 400.0
        assert _strip_price_symbols('400/MT') == 400.0
        assert _strip_price_symbols('USD 350') == 350.0


# ---------------------------------------------------------------------------
# Unit tests — GLiNERExtractor
# ---------------------------------------------------------------------------

class TestGLiNERExtractorUnit:

    def setup_method(self):
        _reset_singleton()

    def test_returns_empty_dict_when_model_unavailable(self):
        from search.services.ner_extractor import GLiNERExtractor
        e = GLiNERExtractor()
        e.__class__._loaded = True
        e.__class__._model = None
        result = e.extract('dextrose suppliers from China')
        assert result['product'] is None
        assert result['origin_country'] is None
        assert result['ner_confidence'] == 1.0

    def test_product_extraction(self):
        entities = [_make_entity('product', 'dextrose anhydrous')]
        e = _make_extractor_with_mock(entities)
        result = e.extract('dextrose anhydrous suppliers')
        assert result['product'] == 'dextrose anhydrous'

    def test_quantity_extraction(self):
        entities = [
            _make_entity('quantity', '50'),
            _make_entity('unit', 'metric tons'),
        ]
        e = _make_extractor_with_mock(entities)
        result = e.extract('I need 50 metric tons of sugar')
        assert result['quantity'] == 50.0
        assert result['unit'] == 'MT'

    def test_quantity_word_number(self):
        entities = [
            _make_entity('quantity', 'fifty'),
            _make_entity('unit', 'metric tons'),
        ]
        e = _make_extractor_with_mock(entities)
        result = e.extract('fifty metric tons of sugar')
        assert result['quantity'] == 50.0

    def test_origin_country_extraction(self):
        entities = [_make_entity('origin_country', 'Brazil')]
        e = _make_extractor_with_mock(entities)
        result = e.extract('dextrose from Brazil')
        assert result['origin_country'] == 'Brazil'

    def test_price_ceiling_extraction(self):
        entities = [_make_entity('price_ceiling', '$400 per MT')]
        e = _make_extractor_with_mock(entities)
        result = e.extract('dextrose under $400/MT')
        assert result['price_ceiling'] == 400.0

    def test_company_name_extraction(self):
        entities = [_make_entity('company_name', 'Nestle')]
        e = _make_extractor_with_mock(entities)
        result = e.extract('has Nestle purchased palm oil')
        assert result['company_name'] == 'Nestle'

    def test_hs_code_extraction(self):
        entities = [_make_entity('hs_code', '1702.30')]
        e = _make_extractor_with_mock(entities)
        result = e.extract('1702.30 suppliers')
        assert result['hs_code'] == '1702.30'

    def test_ner_confidence_is_min_score(self):
        entities = [
            _make_entity('product', 'sugar', score=0.9),
            _make_entity('origin_country', 'Brazil', score=0.6),
        ]
        e = _make_extractor_with_mock(entities)
        result = e.extract('sugar from Brazil')
        assert result['ner_confidence'] == pytest.approx(0.6)

    def test_ner_confidence_one_when_no_entities(self):
        e = _make_extractor_with_mock([])
        result = e.extract('some query')
        assert result['ner_confidence'] == 1.0

    def test_singleton_reuse(self):
        _reset_singleton()
        from search.services.ner_extractor import get_ner_extractor
        e1 = get_ner_extractor()
        e2 = get_ner_extractor()
        assert e1 is e2


# ---------------------------------------------------------------------------
# Unit tests — merge_with_regex
# ---------------------------------------------------------------------------

class TestMergeWithRegex:

    def _extractor(self):
        from search.services.ner_extractor import GLiNERExtractor
        return GLiNERExtractor()

    def test_regex_takes_precedence_for_numeric_fields(self):
        """Regex price_ceiling overrides GLiNER price_ceiling."""
        gliner = {'price_ceiling': 300.0, 'product': 'sugar', 'quantity': None,
                  'unit': None, 'origin_country': None, 'destination_country': None,
                  'price_floor': None, 'hs_code': None, 'company_name': None,
                  'time_period': None, 'ner_confidence': 0.8}
        regex = {'price_ceiling': 400.0}
        merged = self._extractor().merge_with_regex(gliner, regex)
        assert merged['price_ceiling'] == 400.0

    def test_gliner_fills_gap_when_regex_is_none(self):
        """GLiNER product is used when regex product is None."""
        gliner = {'product': 'palm oil', 'quantity': None, 'unit': None,
                  'origin_country': None, 'destination_country': None,
                  'price_ceiling': None, 'price_floor': None, 'hs_code': None,
                  'company_name': None, 'time_period': None, 'ner_confidence': 0.8}
        regex = {'product': None}
        merged = self._extractor().merge_with_regex(gliner, regex)
        assert merged['product'] == 'palm oil'

    def test_both_none_stays_none(self):
        gliner = {'product': None, 'ner_confidence': 1.0}
        regex = {'product': None}
        merged = self._extractor().merge_with_regex(gliner, regex)
        assert merged['product'] is None

    def test_regex_text_overrides_gliner_text(self):
        """Regex company_name overrides GLiNER company_name."""
        gliner = {'company_name': 'Nestle Inc', 'ner_confidence': 0.9}
        regex = {'company_name': 'Nestle Pakistan'}
        merged = self._extractor().merge_with_regex(gliner, regex)
        assert merged['company_name'] == 'Nestle Pakistan'


# ---------------------------------------------------------------------------
# Integration test (real GLiNER model)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestGLiNERIntegration:

    @pytest.fixture(autouse=True)
    def reset(self):
        _reset_singleton()

    @pytest.fixture(autouse=True)
    def check_model(self):
        try:
            from gliner import GLiNER
            GLiNER.from_pretrained('urchade/gliner_medium-v2.1')
        except Exception:
            pytest.skip("GLiNER model not available")

    def test_product_from_trade_query(self):
        from search.services.ner_extractor import GLiNERExtractor
        e = GLiNERExtractor()
        result = e.extract('I need 50 MT of white sugar from Brazil')
        # At minimum product or quantity should be detected
        assert result['product'] is not None or result['quantity'] is not None

    def test_price_ceiling_extraction(self):
        from search.services.ner_extractor import GLiNERExtractor
        e = GLiNERExtractor()
        result = e.extract('dextrose under $400 per metric ton')
        assert result['price_ceiling'] is not None or result['product'] is not None

    def test_company_name_extraction(self):
        from search.services.ner_extractor import GLiNERExtractor
        e = GLiNERExtractor()
        result = e.extract('has Nestle purchased palm oil')
        # GLiNER should detect Nestle as company or palm oil as product
        assert result['company_name'] is not None or result['product'] is not None

    def test_no_crash_on_edge_cases(self):
        from search.services.ner_extractor import GLiNERExtractor
        e = GLiNERExtractor()
        for q in ['', 'a', '!@#$%', '1702.11 1702.30', 'sugar sugar sugar']:
            result = e.extract(q)
            assert isinstance(result, dict)
            assert 'ner_confidence' in result
