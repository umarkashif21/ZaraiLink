# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlu_engine import ModernNLUEngine, extract_product_keyword
from django.contrib.postgres.search import TrigramSimilarity
from trade_data.models import ProductSubCategory, ProductItem

import rapidfuzz

engine = ModernNLUEngine()

FAILING = [
    "buy sugr from brazil",
    "suggar from brazil",
    "sugr cheep frm UAE",
    "suggar cheap frm brazl",
    "molases pakistan",
    "molases suppliers",
    "buy sugr bulk",
    "sugr suppliers from brazil",
]

WORKING = [
    "buy sugar from brazil",
    "sugr cheep",
    "suggar",
    "molas suppliers pak",
    "molasses pakistan",
]

DIVIDER  = "=" * 70
DIVIDER2 = "-" * 70


def trace_subcategory_match(product_keyword: str, country: str = None):
    print(f"  [SUBCAT] product_keyword  → '{product_keyword}'")
    print(f"  [SUBCAT] country arg      → {country!r}")

    if not product_keyword or len(product_keyword) < 2:
        print("  [SUBCAT] SKIPPED — keyword too short")
        return

    from trade_data.models import ProductCategory
    cat_hits = list(ProductCategory.objects.filter(name__icontains=product_keyword).values_list('name', flat=True)[:5])
    print(f"  [SUBCAT] PASS-0 cat icontains → {cat_hits}")

    pass1 = list(ProductSubCategory.objects.filter(name__istartswith=product_keyword).values_list('name', flat=True)[:5])
    print(f"  [SUBCAT] PASS-1 subcat istartswith → {pass1}")

    pass2 = list(ProductItem.objects.filter(name__istartswith=product_keyword).values_list('name', flat=True)[:5])
    print(f"  [SUBCAT] PASS-2 item istartswith → {pass2}")

    if not pass1 and not pass2:
        sc_trig = list(
            ProductSubCategory.objects.annotate(
                sim=TrigramSimilarity('name', product_keyword)
            ).filter(sim__gt=0.3).order_by('-sim').values('name', 'sim')[:5]
        )
        it_trig = list(
            ProductItem.objects.annotate(
                sim=TrigramSimilarity('name', product_keyword)
            ).filter(sim__gt=0.3).order_by('-sim').values('name', 'sim')[:5]
        )
        print(f"  [SUBCAT] PASS-3 trigram subcat (>0.3) → {sc_trig}")
        print(f"  [SUBCAT] PASS-3 trigram items  (>0.3) → {it_trig}")

        best_sc = list(
            ProductSubCategory.objects.annotate(
                sim=TrigramSimilarity('name', product_keyword)
            ).order_by('-sim').values('name', 'sim')[:3]
        )
        best_it = list(
            ProductItem.objects.annotate(
                sim=TrigramSimilarity('name', product_keyword)
            ).order_by('-sim').values('name', 'sim')[:3]
        )
        print(f"  [SUBCAT] PASS-3 TOP-3 subcat (any score) → {best_sc}")
        print(f"  [SUBCAT] PASS-3 TOP-3 items  (any score) → {best_it}")
    else:
        print("  [SUBCAT] PASS-3 SKIPPED (earlier passes found results)")

    if not pass1 and not pass2 and " " in product_keyword:
        words = sorted([w for w in product_keyword.split() if len(w) > 2], key=len, reverse=True)
        print(f"  [SUBCAT] PASS-4 word-by-word, trying words: {words}")
        for word in words:
            p4_sc = list(ProductSubCategory.objects.filter(name__istartswith=word).values_list('name', flat=True)[:5])
            p4_it = list(ProductItem.objects.filter(name__istartswith=word).values_list('name', flat=True)[:5])
            if p4_sc or p4_it:
                print(f"    → word='{word}': subcat={p4_sc}, item={p4_it} ← MATCH!")
                break
            else:
                sc_trig4 = list(
                    ProductSubCategory.objects.annotate(sim=TrigramSimilarity('name', word))
                    .filter(sim__gt=0.3).order_by('-sim').values('name', 'sim')[:3]
                )
                it_trig4 = list(
                    ProductItem.objects.annotate(sim=TrigramSimilarity('name', word))
                    .filter(sim__gt=0.3).order_by('-sim').values('name', 'sim')[:3]
                )
                print(f"    → word='{word}': no istartswith; trigram subcat={sc_trig4}, item={it_trig4}")
                if sc_trig4 or it_trig4:
                    break


def trace_country(query: str):
    from search.services.nlu_engine import ModernNLUEngine
    import re

    q = query.lower()

    _PREP_PATTERNS = [
        r'\b(?:based\s+in|located\s+in)\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
        r'\bwithin\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
        r'\b(?:from|in)\s+([a-z][a-z\s]{1,30}?)(?:\s+(?:and|or|for|that|which|where)\b|$)',
    ]
    for pattern in _PREP_PATTERNS:
        m = re.search(pattern, q)
        if m:
            candidate = m.group(1).strip()
            print(f"  [COUNTRY] Preposition regex captured: '{candidate}'")
            resolved = engine._resolve_country(candidate, cutoff=85.0)
            print(f"  [COUNTRY] RapidFuzz @85 cutoff → '{resolved}'")
            if not resolved:
                STANDARD_COUNTRIES = [
                    "Pakistan", "China", "United States", "India", "Afghanistan",
                    "United Arab Emirates", "Saudi Arabia", "Germany", "United Kingdom",
                    "Australia", "Canada", "Singapore", "Malaysia", "Indonesia",
                    "Turkey", "Brazil", "France", "Italy", "Spain", "Japan", "South Korea",
                    "Vietnam", "Thailand", "Egypt", "South Africa", "Nigeria", "Kenya"
                ]
                match = rapidfuzz.process.extractOne(
                    candidate.lower(), STANDARD_COUNTRIES,
                    scorer=rapidfuzz.fuzz.WRatio,
                    processor=rapidfuzz.utils.default_process,
                    score_cutoff=0
                )
                print(f"  [COUNTRY] RapidFuzz best match (no cutoff) → {match}")
            break
    else:
        print(f"  [COUNTRY] Preposition regex: NO MATCH in query")

    ABBREVIATIONS = {
        "uae": "United Arab Emirates", "uk": "United Kingdom", "usa": "United States",
        "us": "United States", "prc": "China", "ksa": "Saudi Arabia", "pak": "Pakistan",
        "chn": "China", "ger": "Germany", "fra": "France",
    }
    words = re.findall(r'\b\w+\b', q)
    for w in words:
        if w in ABBREVIATIONS:
            print(f"  [COUNTRY] Abbreviation lookup: '{w}' → '{ABBREVIATIONS[w]}'")
            break
    else:
        print(f"  [COUNTRY] Abbreviation lookup: no match")


def run_diagnosis(queries, label):
    print(f"\n{DIVIDER}")
    print(f"  {label}")
    print(DIVIDER)

    for query in queries:
        print(f"\n{'-'*70}")
        print(f"  QUERY: '{query}'")
        print(f"{'-'*70}")

        result = engine.parse(query, ui_context="import")

        print(f"\n  ── STAGE A: NLU Output ──")
        print(f"  intent            : {result.get('intent')}")
        print(f"  product_keyword   : {result.get('product_keyword')!r}")
        print(f"  product (alias)   : {result.get('product')!r}")
        print(f"  country           : {result.get('country')!r}")
        print(f"  origin_country    : {result.get('origin_country')!r}")
        print(f"  entities (GLiNER) : {result.get('entities')}")
        print(f"  price_filter      : {result.get('price_filter')}")
        print(f"  ranking_hint      : {result.get('ranking_hint')!r}")

        sw_keyword = extract_product_keyword(query)
        print(f"\n  ── STAGE B: extract_product_keyword() ──")
        print(f"  stopword keyword  : {sw_keyword!r}")

        entities = result.get("entities", [])
        gliner_product = None
        gliner_country = None
        for ent in entities:
            if ent["label"] in ("product", "commodity", "agricultural product", "trade good"):
                gliner_product = ent["text"]
            if ent["label"] in ("country", "location"):
                gliner_country = ent["text"]
        print(f"\n  ── STAGE C: GLiNER entities detail ──")
        print(f"  GLiNER product span  : {gliner_product!r}")
        print(f"  GLiNER country span  : {gliner_country!r}")
        for ent in entities:
            print(f"    label={ent['label']!r:22} text={ent['text']!r}")

        print(f"\n  ── STAGE D: Country resolution trace ──")
        if gliner_country:
            print(f"  GLiNER gave country span: '{gliner_country}' → resolving @75 cutoff...")
            resolved = engine._resolve_country(gliner_country, cutoff=75.0)
            print(f"  _resolve_country(@75) → {resolved!r}")
            if not resolved:
                STANDARD_COUNTRIES = [
                    "Pakistan","China","United States","India","Afghanistan",
                    "United Arab Emirates","Saudi Arabia","Germany","United Kingdom",
                    "Australia","Canada","Singapore","Malaysia","Indonesia",
                    "Turkey","Brazil","France","Italy","Spain","Japan","South Korea",
                    "Vietnam","Thailand","Egypt","South Africa","Nigeria","Kenya"
                ]
                m = rapidfuzz.process.extractOne(
                    gliner_country.lower(), STANDARD_COUNTRIES,
                    scorer=rapidfuzz.fuzz.WRatio,
                    processor=rapidfuzz.utils.default_process,
                    score_cutoff=0
                )
                print(f"  Raw best RapidFuzz match (no cutoff): {m}")
        else:
            print(f"  GLiNER found no country span → running fallback...")
        trace_country(query)

        print(f"\n  ── STAGE E: Subcategory matcher ──")
        final_keyword = result.get("product_keyword") or result.get("product") or query
        final_country = result.get("country")
        trace_subcategory_match(final_keyword, final_country)

        print()

print(DIVIDER)
print("  ZaraiLink Typo Query Diagnosis")
print(DIVIDER)

run_diagnosis(FAILING, "FAILING QUERIES")
run_diagnosis(WORKING, "WORKING QUERIES")

print(f"\n{DIVIDER}")
print("  Done.")
print(DIVIDER)
