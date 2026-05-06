# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlu_engine import ModernNLUEngine, extract_product_keyword
from search.services.search_service import SearchService
from trade_data.models import ProductSubCategory, ProductItem, Transaction
from django.contrib.postgres.search import TrigramSimilarity

engine = ModernNLUEngine()
svc = SearchService()

DIV = "=" * 65
DIV2 = "-" * 65

QUERIES = [
    "buy sugr from brazil",
    "suggar from brazil",
    "suggar cheap frm brazl",
    "sugr cheep frm UAE",
    # reference
    "buy sugar from brazil",
    "suggar",
]

print(DIV)
print("  RE-DIAGNOSIS after Bug 1 fix")
print(DIV)

for query in QUERIES:
    print(f"\n{DIV2}")
    print(f"  QUERY: {query!r}")
    print(DIV2)

    # 1. NLU output
    nlu = engine.parse(query, ui_context="import")
    kw  = nlu.get("product_keyword", "")
    country = nlu.get("country")
    intent  = nlu.get("intent")
    print(f"  NLU: intent={intent!r}  keyword={kw!r}  country={country!r}")

    # 2. Trace PASS-3 trigram on keyword
    if kw and len(kw) >= 2:
        sc_trig = list(
            ProductSubCategory.objects.annotate(sim=TrigramSimilarity('name', kw))
            .order_by('-sim').values('id', 'name', 'hs_code', 'sim')[:6]
        )
        it_trig = list(
            ProductItem.objects.annotate(sim=TrigramSimilarity('name', kw))
            .order_by('-sim').values('name', 'sub_category_id', 'sub_category__name', 'sub_category__hs_code', 'sim')[:6]
        )
        sc_above = [x for x in sc_trig if x['sim'] > 0.3]
        it_above = [x for x in it_trig if x['sim'] > 0.3]
        print(f"\n  PASS-3 trigram on {kw!r}:")
        print(f"    Subcats >0.3  : {[(x['name'], round(x['sim'],3), x['hs_code']) for x in sc_above]}")
        print(f"    Items   >0.3  : {[(x['name'], round(x['sim'],3), x['sub_category__hs_code']) for x in it_above]}")
        print(f"    Best subcat   : {(sc_trig[0]['name'], round(sc_trig[0]['sim'],3)) if sc_trig else 'none'}")
        print(f"    Best item     : {(it_trig[0]['name'], round(it_trig[0]['sim'],3)) if it_trig else 'none'}")

    # 3. Run _resolve_subcategories to see what subcat_ids are produced
    scope = "IMPORT"
    subcat_ids, variant_list, product_item_ids = svc._resolve_subcategories(
        product_keyword=kw,
        hs_code=None,
        country=country,
        intent=intent,
        scope=scope,
    )
    print(f"\n  _resolve_subcategories:")
    print(f"    subcat_ids   : {subcat_ids}")
    print(f"    variant_list : {[(v['name'], v.get('hs_code')) for v in variant_list]}")

    # 4. Show what transactions actually exist for each returned subcat WITH country filter
    if country and subcat_ids:
        # What the availability filter runs
        country_field = 'origin_country' if intent == 'BUY' else 'destination_country'
        print(f"\n  Availability filter: trade_type=IMPORT, {country_field}={country!r}, subcat_ids={subcat_ids}")
        for sid in subcat_ids:
            sc = ProductSubCategory.objects.filter(id=sid).values('name','hs_code').first()
            txn_count = Transaction.objects.filter(
                trade_type='IMPORT',
                product_item__sub_category_id=sid,
                **{country_field: country}
            ).count()
            txn_any = Transaction.objects.filter(
                trade_type='IMPORT',
                product_item__sub_category_id=sid,
            ).count()
            print(f"    subcat id={sid} ({sc['name'] if sc else '?'} HS:{sc['hs_code'] if sc else '?'}): {txn_count} txns with {country}, {txn_any} total IMPORT txns")

    # 5. Check what Brazil actually has in the full sugar space
    if country == 'Brazil':
        print(f"\n  All IMPORT transactions from Brazil (sugar family):")
        brazil_txns = Transaction.objects.filter(
            trade_type='IMPORT',
            origin_country='Brazil',
            product_item__sub_category__hs_code__startswith='1701',
        ).values(
            'product_item__sub_category__name',
            'product_item__sub_category__hs_code',
            'product_item__sub_category_id',
        ).distinct()
        for t in brazil_txns:
            count = Transaction.objects.filter(
                trade_type='IMPORT',
                origin_country='Brazil',
                product_item__sub_category_id=t['product_item__sub_category_id'],
            ).count()
            print(f"    {t['product_item__sub_category__name']} (HS {t['product_item__sub_category__hs_code']}) id={t['product_item__sub_category_id']} : {count} txns")

    # 6. For UAE queries, what UAE actually sells
    if country == 'United Arab Emirates':
        print(f"\n  All IMPORT transactions from UAE (HS 17xx family):")
        uae_txns = Transaction.objects.filter(
            trade_type='IMPORT',
            origin_country='United Arab Emirates',
            product_item__sub_category__hs_code__startswith='17',
        ).values(
            'product_item__sub_category__name',
            'product_item__sub_category__hs_code',
            'product_item__sub_category_id',
        ).distinct()
        for t in uae_txns:
            print(f"    {t['product_item__sub_category__name']} HS {t['product_item__sub_category__hs_code']} id={t['product_item__sub_category_id']}")

    # 7. Check what execute_search returns (response shape)
    result = svc.execute_search(query, ui_context="import")
    needs_disambig = result.get("needs_disambiguation")
    is_broad = result.get("is_broad_search")
    profiles_count = len(result.get("profiles", []))
    scope_mismatch = result.get("scope_mismatch")
    variants = [(v.get('name'), v.get('hs_code')) for v in result.get("variants", [])]
    print(f"\n  execute_search response:")
    print(f"    needs_disambiguation = {needs_disambig}")
    print(f"    is_broad_search      = {is_broad}")
    print(f"    profiles count       = {profiles_count}")
    print(f"    scope_mismatch       = {scope_mismatch}")
    print(f"    variants             = {variants}")

print(f"\n{DIV}")
print("  Done.")
print(DIV)
