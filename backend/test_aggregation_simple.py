import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction
from django.db.models import Count

# Simple test: Check how aggregation works
print("====== AGGREGATION TEST ======")

# Start with IMPORT trade_type
queryset = Transaction.objects.filter(trade_type='IMPORT')
print(f"Step 1 - IMPORT transactions: {queryset.count()}")

# Add subcategory filter (using a known dextrose subcategory ID)
# First, find a dextrose subcategory
from trade_data.models import ProductSubCategory
dextrose_sub = ProductSubCategory.objects.filter(name__icontains='dextrose').first()
if dextrose_sub:
    print(f"\nUsing subcategory: {dextrose_sub.name} (ID: {dextrose_sub.id})")
    
    queryset = queryset.filter(product_item__sub_category_id=dextrose_sub.id)
    print(f"Step 2 - After subcategory filter: {queryset.count()}")
    
    # Add China filter
    queryset_china = queryset.filter(origin_country='China')
    print(f"Step 3 - After China filter: {queryset_china.count()}")
    
    # Try aggregation
    if queryset_china.exists():
        results = queryset_china.values('seller', 'origin_country').annotate(
            shipment_count=Count('id')
        ).order_by('-shipment_count')[:5]
        
        print(f"\nTop 5 aggregated sellers:")
        for r in results:
            print(f"  {r['seller']} ({r['origin_country']}): {r['shipment_count']} shipments")
else:
    print("No dextrose subcategory found!")
