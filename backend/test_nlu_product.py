import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zarailink.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from search.services.nlu_engine import ModernNLUEngine

engine = ModernNLUEngine()

TEST_QUERIES = [
    "i wanna buy sugar from brazil",
    "who exports sugar products from pakistan",
    "buy sweet stuff used in food industry from brazil",
]

print("\n" + "=" * 60)
print("  NLU Product Extraction — GLiNER sanity check")
print("=" * 60)

for i, q in enumerate(TEST_QUERIES, 1):
    result = engine.parse(q, ui_context="import")
    product  = result.get("product") or "(none)"
    intent   = result.get("intent")
    country  = result.get("country") or "(none)"
    method   = "gliner" if result.get("product") else "fallback"
    timings  = result.get("timings", {})

    gliner_prod_ms = int(timings.get("keybert", 0) * 1000)

    print(f"\n  [{i}] {q!r}")
    print(f"       intent  : {intent}")
    print(f"       country : {country}")
    print(f"       product : {product}")
    print(f"       step4ms : {gliner_prod_ms}ms  (GLiNER product span)")

print("\n" + "=" * 60)
print("  Done.")
print("=" * 60 + "\n")
