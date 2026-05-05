import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlu_engine import ModernNLUEngine

test_queries = [
    "help me find cheap sugar suppliers not sure from where maybe UAE",
    "buy sugar from brazil",
    "buy sugar from anywhere",
    "import dextrose from wherever cheapest",
    "buy sugr from brzail"
]

engine = ModernNLUEngine()

for q in test_queries:
    res = engine.parse(q, ui_context="import")
    print(f"'{q}' -> country={res.get('country')}")
