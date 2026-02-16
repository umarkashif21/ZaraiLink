import os
import django
import sys
from django.db.models import Q

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, ProductItem

def audit_seawall():
    print("--- Auditing Seawall Enterprise - Dextrose Monohydrate ---")
    
    # 1. Find all Dextrose Monohydrate Items
    items = ProductItem.objects.filter(name__icontains="Dextrose Monohydrate")
    item_ids = list(items.values_list('id', flat=True))
    print(f"ProductItem IDs found: {item_ids}")
    
    # 2. Get Raw Count
    # Adjust filter based on what the Aggregator uses (usually trade_type also)
    qs = Transaction.objects.filter(
        seller__icontains="Seawall Enterprise",
        product_item__id__in=item_ids
    )
    
    print(f"Total Transactions in DB: {qs.count()}")
    
    # 3. Check for Exclusions based on Aggregation Logic
    # Aggregator typically filters by:
    # - trade_type (IMPORT/EXPORT based on context)
    # - non-null fields?
    
    print("\n--- Detailed Transaction List ---")
    for tx in qs:
        print(f"ID: {tx.id} | Date: {tx.reporting_date} | Type: {tx.trade_type} | Qty: {tx.qty_mt} | ItemID: {tx.product_item_id}")

    # 4. Check Seller Name Variations
    from django.db.models import Count
    variations = qs.values('seller').annotate(c=Count('id'))
    print("\n--- Seller Name Variations ---")
    for v in variations:
        print(f"Name: '{v['seller']}' -> Count: {v['c']}")

    # 5. Check Trade Type
    export_count = qs.filter(trade_type='EXPORT').count()
    import_count = qs.filter(trade_type='IMPORT').count()
    print(f"\nBreakdown: EXPORT={export_count}, IMPORT={import_count}")

if __name__ == "__main__":
    audit_seawall()
