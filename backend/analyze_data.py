import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from trade_data.models import Transaction, Product, ProductCategory, ProductSubCategory, ProductItem
import pandas as pd
from collections import Counter

print("=" * 60)
print("DATA ANALYSIS FOR LINK PREDICTION")
print("=" * 60)


print("\n=== TRANSACTION DATA ===")
tx_count = Transaction.objects.count()
print(f"Total Transactions: {tx_count}")


buyers = Transaction.objects.values_list('buyer', flat=True).distinct()
sellers = Transaction.objects.values_list('seller', flat=True).distinct()
print(f"Unique Buyers: {len(list(buyers))}")
print(f"Unique Sellers: {len(list(sellers))}")


pairs = Transaction.objects.values_list('buyer', 'seller').distinct()
print(f"Unique Buyer-Seller Pairs: {len(list(pairs))}")


countries = Transaction.objects.values_list('country', flat=True).distinct()
print(f"Unique Countries: {len(list(countries))}")


products = Transaction.objects.values_list('product_item__name', flat=True).distinct()
print(f"Unique Product Items: {len(list(products))}")


print("\n=== SAMPLE TRANSACTIONS ===")
samples = Transaction.objects.all()[:5]
for tx in samples:
    print(f"  Buyer: {tx.buyer[:40]}...")
    print(f"  Seller: {tx.seller[:40]}...")
    print(f"  Product: {tx.product_item.name if tx.product_item else 'N/A'}")
    print(f"  Qty: {tx.qty_mt} MT, USD: ${tx.usd}")
    print(f"  Country: {tx.country}")
    print("-" * 40)


print("\n=== TOP 10 BUYERS (by transaction count) ===")
buyer_counts = Transaction.objects.values_list('buyer', flat=True)
buyer_counter = Counter(buyer_counts)
for buyer, count in buyer_counter.most_common(10):
    print(f"  {buyer[:50]}: {count} transactions")


print("\n=== TOP 10 SELLERS (by transaction count) ===")
seller_counts = Transaction.objects.values_list('seller', flat=True)
seller_counter = Counter(seller_counts)
for seller, count in seller_counter.most_common(10):
    print(f"  {seller[:50]}: {count} transactions")


print("\n=== DATE RANGE ===")
dates = Transaction.objects.exclude(reporting_date__isnull=True).values_list('reporting_date', flat=True)
dates = list(dates)
if dates:
    print(f"  From: {min(dates)}")
    print(f"  To: {max(dates)}")


print("\n=== FEATURES FOR LINK PREDICTION ===")
print("1. Buyer name")
print("2. Seller name")
print("3. Product item (HS code)")
print("4. Country of origin")
print("5. Quantity (MT)")
print("6. Price (USD)")
print("7. Date of transaction")
print("8. Product category hierarchy (Product -> Category -> SubCategory -> Item)")
