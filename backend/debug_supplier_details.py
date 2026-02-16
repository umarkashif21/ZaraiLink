import os
import django
import sys
import json

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.aggregation import SupplierAggregator
from trade_data.models import Transaction, ProductSubCategory

def debug_supplier_details():
    # Find a supplier with transactions
    # Seawall Enterprise Ltd is a good candidate from previous turns
    seller = "Seawall Enterprise Ltd"
    
    # We need subcategory IDs. Dextrose is 717 from previous logs.
    print(f"--- Debugging Supplier Details for: {seller} ---")
    
    agg = SupplierAggregator()
    # Assuming Dextrose SubCat ID is known or we can search it
    # But let's just cheat and check what transactions exist for Seawall
    
    tx = Transaction.objects.filter(seller__icontains="Seawall").first()
    if not tx:
        print("No transactions found for Seawall.")
        return

    subcat_id = tx.product_item.sub_category_id
    print(f"Using SubCategory ID: {subcat_id}")
    
    details = agg.get_supplier_details(seller, [subcat_id])
    
    if details:
        print("\n[History Sample]")
        for h in details['history'][:3]:
            print(f"Buyer: {h['buyer']} | Country Field in JSON: {h['country']}")
            
        print("\n[Filters - Countries]")
        print(details['filters']['countries'])
    else:
        print("No details found.")

    # Also print actual distinct destination countries for this seller from DB
    real_dests = Transaction.objects.filter(seller__icontains=seller).values_list('destination_country', flat=True).distinct()
    print(f"\n[Real DB Destination Countries for {seller}]")
    print(list(real_dests))

if __name__ == "__main__":
    debug_supplier_details()
