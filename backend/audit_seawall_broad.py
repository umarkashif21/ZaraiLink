import os
import django
import sys
from django.db.models import Count

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction

def audit_seawall_products():
    print("--- Seawall Enterprise - All Products ---")
    
    qs = Transaction.objects.filter(seller__icontains="Seawall Enterprise")
    print(f"Total Transactions: {qs.count()}")
    
    # Group by Product Item Name
    print("\n--- By Product Item ---")
    groups = qs.values('product_item__name', 'product_item__id').annotate(c=Count('id')).order_by('-c')
    
    for g in groups:
        p_name = g['product_item__name']
        p_id = g['product_item__id']
        count = g['c']
        print(f"Count: {count} | Item: {p_name} (ID: {p_id})")

    # Check NULL items
    null_count = qs.filter(product_item__isnull=True).count()
    print(f"\nNULL ProductItem Count: {null_count}")

if __name__ == "__main__":
    audit_seawall_products()
