#!/usr/bin/env python
"""
Zarailink Search Engine - Exhaustive QA Test Suite
Runs STANDALONE (no Django server needed for Component 1).
Components 2-7 hit the live API at http://localhost:8000.
"""
import sys
import os
import re
import json
import time
import subprocess
import urllib.request
import urllib.parse

# ── Standalone parser import (no Django required) ─────────────────────────────
PARSER_PATH = os.path.join(os.path.dirname(__file__), 'search', 'services')
sys.path.insert(0, PARSER_PATH)
sys.path.insert(0, os.path.dirname(__file__))

# Monkeypatch Django settings so the parser can import without Django running
import types
_fake_settings = types.ModuleType('django.conf')
class _FakeSettings:
    SEARCH_USE_GLINER_NER = False
    SEARCH_USE_SETFIT = False
_fake_settings.settings = _FakeSettings()
sys.modules.setdefault('django', types.ModuleType('django'))
sys.modules.setdefault('django.conf', _fake_settings)

from query_parser import QueryInterpreter

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

PASS_ICON = f"{GREEN}PASS ✅{RESET}"
FAIL_ICON = f"{RED}FAIL ❌{RESET}"

# ── Helpers ───────────────────────────────────────────────────────────────────
def pq(query, **kwargs):
    """Parse query and return result dict."""
    interp = QueryInterpreter()
    return interp.parse(query, **kwargs)

def check(label, actual, expected, note=''):
    """
    Returns (passed: bool, message: str).
    expected can be a plain value or a callable predicate.
    """
    if callable(expected):
        ok = expected(actual)
    else:
        ok = (actual == expected)
    icon = PASS_ICON if ok else FAIL_ICON
    msg = f"  {icon}  {label}"
    if not ok:
        msg += f"\n         expected: {repr(expected) if not callable(expected) else expected.__doc__}"
        msg += f"\n         actual  : {repr(actual)}"
    if note:
        msg += f"\n         note    : {note}"
    return ok, msg

_total = _passed = 0

def run_check(label, actual, expected, note=''):
    global _total, _passed
    _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        _passed += 1
    return ok

def section(title):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")

def subsection(title):
    print(f"\n{BOLD}  ── {title}{RESET}")

def summary(name, passed, total):
    colour = GREEN if passed == total else (YELLOW if passed >= total*0.8 else RED)
    print(f"\n{colour}{BOLD}  {name}: {passed}/{total} passed{RESET}\n")

def api_get(query, extra_params=''):
    """Hit the live search API. Returns (status_code, json_body)."""
    enc = urllib.parse.quote(query)
    url = f"http://localhost:8000/api/search/?q={enc}&no_cache=1{extra_params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read().decode())
        except Exception:
            pass
        return e.code, body
    except Exception as ex:
        return 0, {"_exception": str(ex)}

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 1: Parser isolation tests
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 1: QueryInterpreter (parser isolation)")

c1_pass = c1_total = 0

def c1(label, actual, expected, note=''):
    global c1_pass, c1_total, _total, _passed
    c1_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c1_pass += 1; _passed += 1
    return ok

# ── Basic intent & family ─────────────────────────────────────────────────────
subsection("Perfect queries — intent & family")

r = pq("dextrose")
c1("dextrose → family=1", r.get('family'), 1)
c1("dextrose → intent=BUY", r.get('intent'), 'BUY')
c1("dextrose → product contains 'dextrose'", r.get('product','').lower(), lambda p: 'dextrose' in p, note="product field should contain dextrose")

r = pq("sugar from Brazil")
c1("sugar from Brazil → country_filter=['Brazil']", r.get('country_filter'), ['Brazil'])
c1("sugar from Brazil → family 1 or 2", r.get('family'), lambda f: f in (1, 2))

r = pq("dextrose over 100 MT")
c1("dextrose over 100 MT → family=3", r.get('family'), 3)
c1("dextrose over 100 MT → volume_mt=100", r.get('volume_mt'), 100.0)

r = pq("sugar avg price below 400")
c1("sugar avg price below 400 → family=4", r.get('family'), 4)
c1("sugar avg price below 400 → price_ceiling=400", r.get('price_ceiling'), 400.0)

r = pq("wheat last 6 months")
c1("wheat last 6 months → family=5", r.get('family'), 5)
c1("wheat last 6 months → time_range set", r.get('time_range'), lambda t: t and 'last' in t.lower())

r = pq("find suppliers of dextrose")
c1("find suppliers of dextrose → intent=BUY", r.get('intent'), 'BUY')

r = pq("export rice to China")
c1("export rice to China → intent=SELL", r.get('intent'), 'SELL')
c1("export rice to China → country_filter contains China", r.get('country_filter'), lambda cf: 'China' in (cf or []))

r = pq("compare countries for sugar imports")
c1("compare countries for sugar imports → family=7", r.get('family'), 7)

r = pq("does Nestle buy dextrose")
c1("does Nestle buy dextrose → family=8", r.get('family'), 8)

# ── Price parsing ─────────────────────────────────────────────────────────────
subsection("Price parsing (floor & ceiling)")

r = pq("dextrose avg price more then 500")
c1("more then 500 → price_floor=500 (typo 'then')", r.get('price_floor'), 500.0)

r = pq("dextrose avg price more than 500")
c1("more than 500 → price_floor=500", r.get('price_floor'), 500.0)

r = pq("dextrose price above 500")
c1("price above 500 → price_floor=500", r.get('price_floor'), 500.0)

r = pq("dextrose over 500 usd")
c1("over 500 usd → price_floor=500", r.get('price_floor'), 500.0,
   note="'over 500 usd' — 'usd' currency suffix; 'over' without size unit should mean price")

r = pq("dextrose below 800")
c1("below 800 → price_ceiling=800", r.get('price_ceiling'), 800.0)

r = pq("dextrose less then 800")
c1("less then 800 → price_ceiling=800 (typo)", r.get('price_ceiling'), 800.0)

r = pq("dextrose cheaper then 800")
c1("cheaper then 800 → price_ceiling=800 (typo)", r.get('price_ceiling'), 800.0)

r = pq("sugar price >600")
c1("sugar price >600 → price_floor=600", r.get('price_floor'), 600.0)

r = pq("sugar price <400")
c1("sugar price <400 → price_ceiling=400", r.get('price_ceiling'), 400.0)

# ── Typo / fuzzy product matching ────────────────────────────────────────────
subsection("Typo / fuzzy product names (product field should not be empty)")

r = pq("suger suppliers")
c1("'suger suppliers' → product not empty", r.get('product',''), lambda p: len(p.strip()) > 0,
   note="product should be 'suger' or similar (fuzzy correction happens in QueryMatcher, not parser)")

r = pq("dekstrose")
c1("'dekstrose' → product not empty", r.get('product',''), lambda p: len(p.strip()) > 0)

r = pq("palm oyl suppliers")
c1("'palm oyl suppliers' → product not empty", r.get('product',''), lambda p: len(p.strip()) > 0)

# ── Volume unit variants ──────────────────────────────────────────────────────
subsection("Volume unit variants")

r = pq("wheat 50 tonnes")
c1("wheat 50 tonnes → volume_mt=50", r.get('volume_mt'), 50.0)

r = pq("wheat 50 tons")
c1("wheat 50 tons → volume_mt=50", r.get('volume_mt'), 50.0)

r = pq("wheat 50 ton")
c1("wheat 50 ton → volume_mt=50", r.get('volume_mt'), 50.0)

r = pq("wheat 50 kgs")
c1("wheat 50 kgs → volume_mt extracted (0.05)", r.get('volume_mt'), lambda v: v is not None and v > 0)

r = pq("wheat 50 kilograms")
c1("wheat 50 kilograms → volume extracted", r.get('volume_mt'), lambda v: v is not None and v > 0)

r = pq("100 metric ton dextrose")
c1("100 metric ton dextrose → volume_mt=100", r.get('volume_mt'), 100.0)

# ── Time parsing ──────────────────────────────────────────────────────────────
subsection("Time / date parsing")

r = pq("dextrose Q1 2024")
c1("dextrose Q1 2024 → time_range set", r.get('time_range'), lambda t: t and 'Q1' in (t or '').upper())

r = pq("dextrose jan 2024")
c1("dextrose jan 2024 → time_range set", r.get('time_range'), lambda t: t is not None)

r = pq("dextrose 2023")
c1("dextrose 2023 → time_range set", r.get('time_range'), lambda t: t is not None)

r = pq("dextrose last year")
c1("dextrose last year → time_range set", r.get('time_range'), lambda t: t is not None)

r = pq("dextrose last 3 months")
c1("dextrose last 3 months → time_range set", r.get('time_range'), lambda t: t and '3' in (t or ''))

r = pq("dextrose since january")
c1("dextrose since january → time_range set", r.get('time_range'), lambda t: t is not None)

# ── Family 6 ──────────────────────────────────────────────────────────────────
subsection("Family 6 — Top N")

r = pq("top 5 dextrose suppliers")
c1("top 5 dextrose suppliers → family=6", r.get('family'), 6)
c1("top 5 dextrose suppliers → intent=BUY", r.get('intent'), 'BUY')

r = pq("best 3 sugar buyers")
c1("best 3 sugar buyers → family=6", r.get('family'), 6)
c1("best 3 sugar buyers → intent=SELL", r.get('intent'), 'SELL')

# ── Intent — sell-side ────────────────────────────────────────────────────────
subsection("Intent — sell-side phrases")

r = pq("who buys cotton")
c1("who buys cotton → intent=SELL", r.get('intent'), 'SELL')

r = pq("find buyers for rice")
c1("find buyers for rice → intent=SELL", r.get('intent'), 'SELL')

r = pq("sell cotton")
c1("sell cotton → intent=SELL", r.get('intent'), 'SELL')

# ── Country filter normalisation ──────────────────────────────────────────────
subsection("Country filter — case sensitivity")

r = pq("import wheat from Canada")
c1("import wheat from Canada → intent=BUY", r.get('intent'), 'BUY')
c1("import wheat from Canada → country=['Canada']", r.get('country_filter'), lambda cf: 'Canada' in (cf or []))

r = pq("dextrose from china")
c1("dextrose from china (lowercase) → country includes China", r.get('country_filter'), lambda cf: 'China' in (cf or []))

r = pq("dextrose from CHINA")
c1("dextrose from CHINA (uppercase) → country includes China", r.get('country_filter'), lambda cf: 'China' in (cf or []))

# ── Edge cases ────────────────────────────────────────────────────────────────
subsection("Edge cases & robustness")

r = pq("")
c1("empty string → {} or empty dict", r, lambda res: res == {} or (isinstance(res, dict) and not res.get('product')))

r = pq("     ")
c1("whitespace-only → graceful (no crash)", r, lambda res: isinstance(res, dict))

r = pq("<script>alert('xss')</script>")
c1("XSS string → no crash, returns dict", r, lambda res: isinstance(res, dict))

r = pq("a")
c1("single letter → no crash", r, lambda res: isinstance(res, dict))

r = pq("dextrose and sugar")
c1("'dextrose and sugar' → multi_intent or family 1", r, lambda res: isinstance(res, dict))

r = pq("1702.30")
c1("HS code '1702.30' → no crash", r, lambda res: isinstance(res, dict))

r = pq("hs code 1702")
c1("'hs code 1702' → no crash", r, lambda res: isinstance(res, dict))

r = pq("دیکسٹروز")
c1("Urdu 'dextrose' → no crash", r, lambda res: isinstance(res, dict))

r = pq("500")
c1("Only number '500' → no crash", r, lambda res: isinstance(res, dict))

r = pq("@@@@")
c1("Only symbols '@@@@' → no crash", r, lambda res: isinstance(res, dict))

long_q = "dextrose " * 60
r = pq(long_q.strip())
c1("Very long query (480 chars) → no crash", r, lambda res: isinstance(res, dict))

r = pq("sugar'; DROP TABLE transactions;--")
c1("SQL injection → no crash, returns dict", r, lambda res: isinstance(res, dict))

summary("Component 1", c1_pass, c1_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 2: Price Filter in Aggregation (live API)
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 2: Price Filter (live API)")

c2_pass = c2_total = 0

def c2(label, actual, expected, note=''):
    global c2_pass, c2_total, _total, _passed
    c2_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c2_pass += 1; _passed += 1
    return ok

def check_price_floor(query, floor):
    code, body = api_get(query)
    results = body.get('results', [])
    parsed = body.get('parsed_query', {})
    c2(f"'{query}' → HTTP 200", code, 200)
    c2(f"'{query}' → price_floor parsed = {floor}", parsed.get('price_floor'), floor)
    if results:
        violations = [r for r in results if r.get('avg_price', 0) < floor]
        c2(f"'{query}' → ALL results have avg_price >= {floor} ({len(results)} results)",
           len(violations), 0,
           note=f"violations: {[(r.get('name'), r.get('avg_price')) for r in violations[:3]]}" if violations else '')

def check_price_ceiling(query, ceiling):
    code, body = api_get(query)
    results = body.get('results', [])
    parsed = body.get('parsed_query', {})
    c2(f"'{query}' → HTTP 200", code, 200)
    c2(f"'{query}' → price_ceiling parsed = {ceiling}", parsed.get('price_ceiling'), ceiling)
    if results:
        violations = [r for r in results if r.get('avg_price', 0) > ceiling]
        c2(f"'{query}' → ALL results have avg_price <= {ceiling} ({len(results)} results)",
           len(violations), 0,
           note=f"violations: {[(r.get('name'), r.get('avg_price')) for r in violations[:3]]}" if violations else '')

check_price_floor("dextrose price above 500", 500.0)
check_price_floor("sugar more than 600", 600.0)
check_price_ceiling("dextrose below 800", 800.0)

# Test "between" — check parsed values only
code, body = api_get("dextrose between 400 and 800")
parsed = body.get('parsed_query', {})
c2("'dextrose between 400 and 800' → no crash", code, lambda c: c in (200, 400))

summary("Component 2", c2_pass, c2_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 3: Volume Filter
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 3: Volume Filter (live API)")

c3_pass = c3_total = 0

def c3(label, actual, expected, note=''):
    global c3_pass, c3_total, _total, _passed
    c3_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c3_pass += 1; _passed += 1
    return ok

code, body = api_get("dextrose over 100 MT")
results = body.get('results', [])
parsed = body.get('parsed_query', {})
c3("'dextrose over 100 MT' → HTTP 200", code, 200)
c3("'dextrose over 100 MT' → volume_mt=100 parsed", parsed.get('volume_mt'), 100.0)
if results:
    has_volume_fit = all('volume_fit' in r for r in results)
    c3("'dextrose over 100 MT' → all results have volume_fit field", has_volume_fit, True)
    c3("'dextrose over 100 MT' → results returned", len(results), lambda n: n > 0)

summary("Component 3", c3_pass, c3_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 4: Country Filter
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 4: Country Filter (live API)")

c4_pass = c4_total = 0

def c4(label, actual, expected, note=''):
    global c4_pass, c4_total, _total, _passed
    c4_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c4_pass += 1; _passed += 1
    return ok

def check_country_filter(query, expected_country):
    code, body = api_get(query)
    results = body.get('results', [])
    parsed = body.get('parsed_query', {})
    c4(f"'{query}' → HTTP 200", code, 200)
    c4(f"'{query}' → country_filter contains '{expected_country}'",
       expected_country in (parsed.get('country_filter') or []), True)
    if results:
        violations = [r for r in results if r.get('country') != expected_country]
        c4(f"'{query}' → ALL results from {expected_country} ({len(results)} results)",
           len(violations), 0,
           note=f"violations: {[(r.get('name'), r.get('country')) for r in violations[:3]]}" if violations else '')

check_country_filter("dextrose from China", "China")
check_country_filter("dextrose from Germany", "Germany")
check_country_filter("dextrose from india", "India")

summary("Component 4", c4_pass, c4_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 5: Time Filter
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 5: Time Filter (live API)")

c5_pass = c5_total = 0

def c5(label, actual, expected, note=''):
    global c5_pass, c5_total, _total, _passed
    c5_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c5_pass += 1; _passed += 1
    return ok

code, body = api_get("dextrose last 6 months")
parsed = body.get('parsed_query', {})
c5("'dextrose last 6 months' → time_range set", parsed.get('time_range'), lambda t: t is not None)

code, body = api_get("sugar 2023")
parsed = body.get('parsed_query', {})
c5("'sugar 2023' → time_range set", parsed.get('time_range'), lambda t: t is not None)

summary("Component 5", c5_pass, c5_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 6: Intent (BUY vs SELL)
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 6: Intent (BUY vs SELL) — live API")

c6_pass = c6_total = 0

def c6(label, actual, expected, note=''):
    global c6_pass, c6_total, _total, _passed
    c6_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c6_pass += 1; _passed += 1
    return ok

code, body = api_get("find suppliers of dextrose")
parsed = body.get('parsed_query', {})
results = body.get('results', [])
c6("'find suppliers of dextrose' → intent=BUY", parsed.get('intent'), 'BUY')
if results:
    c6("'find suppliers of dextrose' → results type=Supplier", results[0].get('type'), 'Supplier')

code, body = api_get("find buyers for dextrose")
parsed = body.get('parsed_query', {})
results = body.get('results', [])
c6("'find buyers for dextrose' → intent=SELL", parsed.get('intent'), 'SELL')

code, body = api_get("who exports cotton")
parsed = body.get('parsed_query', {})
c6("'who exports cotton' → intent=SELL", parsed.get('intent'), 'SELL')

summary("Component 6", c6_pass, c6_total)

# ══════════════════════════════════════════════════════════════════════════════
# COMPONENT 7: Edge Cases & Robustness (live API)
# ══════════════════════════════════════════════════════════════════════════════
section("COMPONENT 7: Edge Cases & Robustness (live API)")

c7_pass = c7_total = 0

def c7(label, actual, expected, note=''):
    global c7_pass, c7_total, _total, _passed
    c7_total += 1; _total += 1
    ok, msg = check(label, actual, expected, note)
    print(msg)
    if ok:
        c7_pass += 1; _passed += 1
    return ok

# Empty string → 400
code, body = api_get("")
c7("Empty string query → 400", code, 400)

# Very long query
long_q = "dextrose " * 60
code, body = api_get(long_q.strip())
c7("Very long query (480 chars) → no 500", code, lambda c: c != 500)

# SQL injection
code, body = api_get("sugar'; DROP TABLE transactions;--")
c7("SQL injection → no 500", code, lambda c: c != 500)

# Only numbers
code, body = api_get("500")
c7("'500' only → no 500 error", code, lambda c: c != 500)

# Only symbols
code, body = api_get("@@@@")
c7("'@@@@' only → no 500 error", code, lambda c: c != 500)

# Unicode
code, body = api_get("دیکسٹروز")
c7("Urdu 'dextrose' → no 500 error", code, lambda c: c != 500)

summary("Component 7", c7_pass, c7_total)

# ══════════════════════════════════════════════════════════════════════════════
# GRAND TOTAL
# ══════════════════════════════════════════════════════════════════════════════
section("GRAND TOTAL")
colour = GREEN if _passed == _total else (YELLOW if _passed >= _total * 0.9 else RED)
print(f"\n{colour}{BOLD}  OVERALL: {_passed}/{_total} tests passed{RESET}")
if _passed < _total:
    print(f"\n{RED}  {_total - _passed} tests FAILED — see above for details.{RESET}")
else:
    print(f"\n{GREEN}  All tests passed!{RESET}")
print()
