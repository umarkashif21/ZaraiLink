"""
Check DB Units for Sugar/Chocolate.
"""
import os
import django
import sys

# Setup Django
sys.path.append(r'c:\Users\Dell\Documents\ZaraiLink\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction
from django.db.models import Max, Avg, Count

def check_product(keyword):
    print(f"\n--- Checking '{keyword}' ---")
    txs = Transaction.objects.filter(product_item__sub_category__name__icontains=keyword)
    count = txs.count()
    print(f"Total Transactions: {count}")
    
    if count == 0:
        return

    # Check units
    stats = txs.aggregate(
        max_mt=Max('qty_mt'),
        avg_price_mt=Avg('usd_per_mt'),
        max_price_mt=Max('usd_per_mt'),
        avg_price_kg=Avg('usd_per_kg'),
        max_price_kg=Max('usd_per_kg')
    )
    print("Aggregate Stats:")
    print(f"  Max Volume (MT): {stats['max_mt']}")
    print(f"  Avg Price (USD/MT): {stats['avg_price_mt']}")
    print(f"  Max Price (USD/MT): {stats['max_price_mt']}")
    print(f"  Avg Price (USD/kg): {stats['avg_price_kg']}")
    
    # Check sample sample where price > 100
    high_price = txs.filter(usd_per_mt__gt=100).count()
    print(f"  Count with Price/MT > 100: {high_price}")
    
    # Check Afghanistan specific
    afghan = txs.filter(destination_country__icontains='Afghanistan')
    print(f"  Exports to Afghanistan: {afghan.count()}")
    if afghan.exists():
        af_stats = afghan.aggregate(
             max_price_mt=Max('usd_per_mt'),
             avg_price_mt=Avg('usd_per_mt')
        )
        print(f"  Afghanistan Max Price (USD/MT): {af_stats['max_price_mt']}")

if __name__ == "__main__":
    check_product("sugar")
    check_product("chocolate")
