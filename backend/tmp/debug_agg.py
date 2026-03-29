import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, ProductItem
from django.db.models import F, Sum, Count, FloatField

def debug_aggs():
    search_term = "FUFENG"
    print(f"--- Searching for '{search_term}' ---")
    
    # Find exact seller name
    seller_match = Transaction.objects.filter(seller__icontains=search_term).values_list('seller', flat=True).distinct().first()
    print(f"Match found in DB: {seller_match}")
    
    if not seller_match:
        print("No matching seller found.")
        return

    # 1. Total transactions
    count = Transaction.objects.filter(seller=seller_match).count()
    print(f"Total transactions for {seller_match}: {count}")
    
    # 2. Check product_item status
    with_item = Transaction.objects.filter(
        seller=seller_match,
        product_item__isnull=False
    ).count()
    print(f"With ProductItem: {with_item}")
    
    # 3. Print sample row
    sample = Transaction.objects.filter(seller=seller_match).first()
    if sample:
        print(f"Sample Row: {sample.seller} | Item: {sample.product_item_id} | Raw HS: {sample.hs_code}")

    # 4. Try the subcat aggregation
    results = (
        Transaction.objects.filter(seller=seller_match, product_item__sub_category__isnull=True).count()
    )
    print(f"Count with NULL Subcategory: {results}")

    # 5. Correct aggregation
    print(f"Grouping by subcat for {seller_match}...")
    qs = Transaction.objects.filter(seller=seller_match, product_item__sub_category__isnull=False)
    aggs = qs.values(subcat_id=F('product_item__sub_category_id'), pname=F('product_item__sub_category__name')).annotate(v=Sum('qty_mt'))
    
    first_subcat_id = None
    for a in aggs:
        print(f"  - {a['pname']} (ID: {a['subcat_id']}): {a['v']} MT")
        if first_subcat_id is None: first_subcat_id = a['subcat_id']

    # 6. Check Trend
    if first_subcat_id:
        print(f"Checking trend for subcat ID: {first_subcat_id}...")
        from django.db.models.functions import TruncMonth
        trend = (
            Transaction.objects.filter(seller=seller_match, product_item__sub_category_id=first_subcat_id)
            .annotate(month=TruncMonth('reporting_date'))
            .values('month')
            .annotate(
                volume=Sum('qty_mt'),
                avg_price=Sum(F('qty_mt') * F('usd_per_mt'), output_field=FloatField()) / Sum('qty_mt', output_field=FloatField())
            )
            .order_by('month')
        )
        print(f"Trend results count: {len(trend)}")
        for t in trend:
            print(f"  - {t['month']}: {t['avg_price']} USD/MT")

if __name__ == "__main__":
    from django.db import models
    debug_aggs()
