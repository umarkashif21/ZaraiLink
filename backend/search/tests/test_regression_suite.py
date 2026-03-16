"""
backend/search/tests/test_regression_suite.py

Phase 8: CI regression guard — 20 golden queries with expected behavior.

These tests verify:
  1. No crashes across all 9 query families
  2. Correct family classification for clear-signal queries
  3. Correct intent (BUY vs SELL)
  4. Key fields populated (product, family, intent)
  5. No regression on previously-fixed edge cases

Run:
    cd backend
    pytest search/tests/test_regression_suite.py -v
"""

import pytest


@pytest.fixture(scope='module')
def interpreter():
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
    try:
        django.setup()
    except RuntimeError:
        pass
    from search.services.query_parser import QueryInterpreter
    return QueryInterpreter()


# ── Helper ────────────────────────────────────────────────────────────────────

def parse(interpreter, query, explicit_scope=None):
    return interpreter.parse(query, explicit_scope=explicit_scope)


# ── Regression tests ──────────────────────────────────────────────────────────

class TestRegressionSuite:

    # R01: Basic BUY — should return family 1 or 3 (if volume present)
    def test_r01_basic_buy_dextrose(self, interpreter):
        r = parse(interpreter, "find dextrose suppliers")
        assert r.get('intent') == 'BUY'
        assert r.get('family') in (1, 3)
        assert 'dextrose' in (r.get('product') or '').lower()

    # R02: Basic SELL
    def test_r02_basic_sell(self, interpreter):
        r = parse(interpreter, "who buys wheat")
        assert r.get('intent') == 'SELL'

    # R03: F3 Volume
    def test_r03_volume_query(self, interpreter):
        r = parse(interpreter, "100 MT dextrose suppliers")
        assert r.get('family') == 3
        assert r.get('volume_mt') == pytest.approx(100.0, abs=1.0)

    # R04: F4 Price ceiling
    def test_r04_price_ceiling(self, interpreter):
        r = parse(interpreter, "dextrose under $400/MT")
        assert r.get('family') == 4
        assert r.get('price_ceiling') == pytest.approx(400.0, abs=1.0)

    # R05: F4 Price floor
    def test_r05_price_floor(self, interpreter):
        r = parse(interpreter, "sugar above $350")
        assert r.get('family') == 4
        assert r.get('price_floor') == pytest.approx(350.0, abs=1.0)

    # R06: F5 Time — quarter+year triggers F5
    def test_r06_time_year(self, interpreter):
        r = parse(interpreter, "Q1 2024 sugar suppliers")
        assert r.get('family') == 5

    # R07: F5 Time — relative
    def test_r07_time_last_6_months(self, interpreter):
        r = parse(interpreter, "last 6 months cotton exporters")
        assert r.get('family') == 5

    # R08: F6 TopK
    def test_r08_topk(self, interpreter):
        r = parse(interpreter, "top 5 palm oil exporters")
        assert r.get('family') == 6

    # R09: F7 Country comparison
    def test_r09_country_compare(self, interpreter):
        r = parse(interpreter, "which countries import most sugar")
        assert r.get('family') == 7

    # R10: F8 Evidence
    def test_r10_evidence(self, interpreter):
        r = parse(interpreter, "has Nestle purchased palm oil")
        assert r.get('family') == 8

    # R11: Multi-intent split on semicolon
    def test_r11_multi_intent_semicolon(self, interpreter):
        r = parse(interpreter, "dextrose suppliers; who buys wheat")
        assert r.get('multi_intent') is True
        assert r.get('family') == 9

    # R12: Country filter extracted
    def test_r12_country_filter_china(self, interpreter):
        r = parse(interpreter, "buy cotton from China")
        assert 'China' in r.get('country_filter', [])

    # R13: Country filter extracted — India
    def test_r13_country_filter_india(self, interpreter):
        r = parse(interpreter, "wheat flour suppliers from India")
        assert 'India' in r.get('country_filter', [])

    # R14: SELL intent with "sell" keyword
    def test_r14_sell_keyword(self, interpreter):
        r = parse(interpreter, "I want to sell my dextrose")
        assert r.get('intent') == 'SELL'

    # R15: F4 price query — explicit ceiling triggers family 4
    def test_r15_price_ceiling_triggers_f4(self, interpreter):
        r = parse(interpreter, "dextrose anhydrous cheaper than $380")
        assert r.get('family') == 4
        assert r.get('price_ceiling') == pytest.approx(380.0, abs=1.0)

    # R16: F8 triggered by "has ... bought" pattern
    def test_r16_f8_has_bought_pattern(self, interpreter):
        r = parse(interpreter, "has ICI Pakistan bought starch")
        assert r.get('family') == 8

    # R17: Output always has required fields
    def test_r17_output_fields(self, interpreter):
        r = parse(interpreter, "sugar exporters from Brazil")
        for field in ('intent', 'family', 'product', 'scope', 'multi_intent'):
            assert field in r, f"Missing field: {field}"

    # R18: Empty query returns empty dict (no crash)
    def test_r18_empty_query_no_crash(self, interpreter):
        r = parse(interpreter, "")
        assert r == {}

    # R19: Worldwide scope default
    def test_r19_default_scope_worldwide(self, interpreter):
        r = parse(interpreter, "find dextrose suppliers")
        assert r.get('scope') == 'WORLDWIDE'

    # R20: Explicit scope override
    def test_r20_explicit_scope_pakistan(self, interpreter):
        r = parse(interpreter, "find dextrose suppliers", explicit_scope='PAKISTAN')
        assert r.get('scope') == 'PAKISTAN'


# ── Smoke tests (no crash for diverse inputs) ─────────────────────────────────

SMOKE_QUERIES = [
    "sugar",
    "   ",
    "buy 500 MT lactose monohydrate from Europe",
    "top 10 tapioca starch sellers worldwide",
    "Q1 2024 sugar exporters",
    "has Unilever Pakistan purchased palm oil",
    "which country imports most wheat starch",
    "sell our glucose syrup; find buyers for calcium carbonate",
    "cheap wheat suppliers under $400",
    "recent 2024 glucose importers",
]

class TestSmokeNocrash:

    @pytest.mark.parametrize("query", SMOKE_QUERIES)
    def test_no_crash(self, interpreter, query):
        """Pipeline must never raise for any query string."""
        try:
            result = interpreter.parse(query)
            # Result is either empty dict (blank query) or has intent/family
            if result:
                assert 'family' in result
        except Exception as e:
            pytest.fail(f"parse() raised for query {query!r}: {e}")
