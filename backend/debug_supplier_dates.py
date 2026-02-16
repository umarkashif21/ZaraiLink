import os
import django
import sys
import json

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.aggregation import SupplierAggregator
from trade_data.models import Transaction

def debug_supplier_dates():
    seller = "Seawall Enterprise Ltd"
    print(f"--- Debugging Dates for: {seller} ---")
    
    # Get Subcat for Dextrose
    tx = Transaction.objects.filter(seller__icontains="Seawall").first()
    if not tx:
        print("No transactions found.")
        return
        
    subcat_id = tx.product_item.sub_category_id
    
    agg = SupplierAggregator()
    details = agg.get_supplier_details(seller, [subcat_id])
    
    if details:
        print(f"Total History Items: {len(details['history'])}")
        print("\n[Date Sample]")
        for h in details['history'][:10]:
            print(f"Date: {h['date']} | Original DB Value: {type(h['date'])} | Buyer: {h['buyer']}")
    else:
        print("No details found.")

if __name__ == "__main__":
    debug_supplier_dates()
