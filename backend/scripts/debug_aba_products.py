import os
import django
import sys
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.services.products import get_company_product_performance, get_volume_share
from trade_data.models import Transaction, ProductItem

COMPANY_NAME = "Aba Stepsworth Dwc Llc"

def debug_company_products():
    print(f"--- Debugging Products for: {COMPANY_NAME} ---")
    
    
    as_buyer = Transaction.objects.filter(buyer=COMPANY_NAME).count()
    as_seller = Transaction.objects.filter(seller=COMPANY_NAME).count()
    print(f"Transaction Count -> Buyer: {as_buyer}, Seller: {as_seller}")
    
    direction = 'import' if as_buyer > 0 else 'export'
    if as_seller > as_buyer:
        direction = 'export'
    
    print(f"Assumed Direction: {direction}")

    
    try:
        print("\nCalling get_company_product_performance...")
        performance = list(get_company_product_performance(
            company_name=COMPANY_NAME,
            direction=direction
        ))
        print(f"Performance entries: {len(performance)}")
        for p in performance[:3]:
            print(f" - {p}")
            
    except Exception as e:
        print(f"!!! ERROR in get_company_product_performance: {e}")
        import traceback
        traceback.print_exc()

    
    try:
        print("\nCalling get_volume_share...")
        shares = list(get_volume_share(
            company_name=COMPANY_NAME,
            direction=direction
        ))
        print(f"Share entries: {len(shares)}")
        for s in shares[:3]:
            print(f" - {s}")
            
    except Exception as e:
        print(f"!!! ERROR in get_volume_share: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_company_products()
