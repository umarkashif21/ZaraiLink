"""
Inspect Export Data for Chocolate and Sugar.
Check availablity of Countries, Volumes, and Prices.
"""
import os
import django
import sys

# Setup Django Environment
import os
import sys

# Add CWD to sys.path
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)
print(f"DEBUG: sys.path = {sys.path}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from trade_data.models import Transaction, SubCategory
from django.db.models import Count, Max, Min, Avg

def check_product(product_name):
    print(f"\n--- Checking Product: {product_name} ---")
    
    # 1. Find Subcategories
    subs = SubCategory.objects.filter(name__icontains=product_name)
    print(f"Subcategories found: {[s.name for s in subs]}")
    sub_ids = subs.values_list('id', flat=True)
    
    if not sub_ids:
        print("❌ No subcategories found!")
        return

    # 2. Check EXPORT Transactions
    qs = Transaction.objects.filter(
        trade_type='EXPORT',
        product_item__sub_category__in=sub_ids
    )
    count = qs.count()
    print(f"Total EXPORT Transactions: {count}")
    
    if count == 0:
        return

    # 3. Check Countries (Destination)
    countries = qs.values('destination_country').annotate(c=Count('id')).order_by('-c')
    print(f"Top 5 Destinations: {list(countries)[:5]}")
    
    # Check specific countries mentioned by user
    for country in ['Italy', 'Afghanistan']:
        exists = qs.filter(destination_country__iexact=country).count()
        print(f"  Exports to {country}: {exists}")

    # 4. Check Volume Stats
    vol_stats = qs.aggregate(
        min_vol=Min('qty_mt'),
        max_vol=Max('qty_mt'),
        avg_vol=Avg('qty_mt')
    )
    print(f"Volume Stats (MT): {vol_stats}")
    
    # Check 100MT availability
    start_100 = qs.filter(qty_mt__gte=100).count()
    print(f"  Shipments >= 100MT: {start_100}")

    # 5. Check Price Stats
    price_stats = qs.aggregate(
        min_price=Min('usd_per_mt'),
        max_price=Max('usd_per_mt'),
        avg_price=Avg('usd_per_mt')
    )
    print(f"Price Stats ($/MT): {price_stats}")
    
    # Check > $500
    above_500 = qs.filter(usd_per_mt__gt=500).count()
    print(f"  Prices > $500: {above_500}")

if __name__ == "__main__":
    check_product("chocolate")
    check_product("sugar") # For refined sugar
    check_product("dextrose")
