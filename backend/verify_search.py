"""
Quick diagnostic to verify the revamped search pipeline.
Run: python verify_search.py
"""
import django, os, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlu_engine import extract_product_keyword, ModernNLUEngine
from search.services.search_service import SearchService

print("\n" + "="*65)
print("  1. KEYWORD EXTRACTION TESTS")
print("="*65)
cases = [
    ("i want to buy dextrose anhydrous", "dextrose anhydrous"),
    ("find buyers for basmati rice",     "basmati rice"),
    ("I WANT TO SELL fruc",              "fruc"),
    ("dex",                              "dex"),
    ("looking for suppliers of urea 46%","urea 46"),
    ("sugar under 500",                  "sugar"),
    ("I want to sell wheat to china",    "wheat china"),
]
all_ok = True
for query, expected_contains in cases:
    kw = extract_product_keyword(query)
    ok = expected_contains.split()[0].lower() in kw.lower()
    status = "OK" if ok else "FAIL"
    if not ok:
        all_ok = False
    print(f"  [{status}] {query!r}")
    print(f"        → {kw!r}  (expected to contain: {expected_contains!r})")

print("\n" + "="*65)
print("  2. AUTOCOMPLETE TESTS")
print("="*65)
svc = SearchService()

for partial in ["i want to buy dex", "dex", "fruc", "urea"]:
    results = svc.autocomplete_products(partial, limit=5)
    names = [r['name'] for r in results]
    print(f"  autocomplete({partial!r}) -> {names}")

print("\n" + "="*65)
print("  3. FULL SEARCH TESTS")
print("="*65)

# Test: unambiguous product
r = svc.execute_search("i want to buy dextrose anhydrous", ui_context="worldwide")
print(f"\n  [Exact - BUY dextrose anhydrous, worldwide]")
print(f"  intent={r['nlu']['intent']}, keyword={r['nlu'].get('product_keyword')}")
print(f"  profiles={len(r['profiles'])}, disambig={r.get('needs_disambiguation')}, engine={r.get('search_engine')}")
if r['profiles']:
    p = r['profiles'][0]
    print(f"  Top result: {p['company_name']} | vol={p['total_volume']:.1f} | price={p['avg_price']:.2f}")

# Test: ambiguous query (should trigger disambiguation)
r2 = svc.execute_search("dex", ui_context="worldwide")
print(f"\n  [Ambiguous - 'dex', worldwide]")
print(f"  disambig={r2.get('needs_disambiguation')}, variants={[v['name'] for v in r2.get('variants', [])]}")

# Test: SELL intent
r3 = svc.execute_search("find buyers for basmati rice", ui_context="worldwide")
print(f"\n  [SELL intent - buyers for rice, worldwide]")
print(f"  intent={r3['nlu']['intent']}, profiles={len(r3['profiles'])}")

# Test: Pakistan scope
r4 = svc.execute_search("i want to buy sugar", ui_context="pakistan")
print(f"\n  [Pakistan scope - buy sugar]")
print(f"  intent={r4['nlu']['intent']}, profiles={len(r4['profiles'])}, engine={r4.get('search_engine')}")

print("\n" + "="*65)
print("  DONE" + (" — All keyword tests PASSED" if all_ok else " — SOME KEYWORD TESTS FAILED"))
print("="*65 + "\n")
