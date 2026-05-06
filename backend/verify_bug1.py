# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlu_engine import ModernNLUEngine, extract_product_keyword
engine = ModernNLUEngine()

queries = [
    ("buy sugr from brazil",      "sugr"),
    ("suggar from brazil",         "suggar"),
    ("sugr suppliers from brazil", "sugr"),
    ("suggar cheap frm brazl",     "suggar"),
    ("sugr cheep frm UAE",         "sugr"),
    # Controls - should be unchanged
    ("buy sugar from brazil",      "sugar"),
    ("suggar",                     "suggar"),
]

print("Bug 1 fix verification\n" + "="*55)
all_pass = True
for query, expected_contains in queries:
    r = engine.parse(query, ui_context="import")
    kw = r.get("product_keyword", "")
    country = r.get("country", "")
    has_preposition = any(p in kw.split() for p in ["from", "frm", "in"])
    ok = (expected_contains in kw) and not has_preposition
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{status}] {query!r}")
    print(f"         product_keyword = {kw!r}  (expected to contain {expected_contains!r})")
    print(f"         country         = {country!r}")
    print()

print("="*55)
print("Overall:", "ALL PASS" if all_pass else "SOME FAILURES")
