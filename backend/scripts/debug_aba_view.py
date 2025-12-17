import os
import django
import sys
import json
from django.http import HttpRequest


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.views import company_products_api

COMPANY_NAME = "Aba Stepsworth Dwc Llc"

def debug_view():
    print(f"--- Debugging View for: {COMPANY_NAME} ---")
    request = HttpRequest()
    request.method = 'GET'
    
    
    
    request.GET['direction'] = 'export'
    request.META['SERVER_NAME'] = 'localhost'
    request.META['SERVER_PORT'] = '8000' 

    try:
        response = company_products_api(request, COMPANY_NAME)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = json.loads(response.content)
            perf = content.get('product_performance', [])
            print(f"Product Performance Items: {len(perf)}")
            if len(perf) > 0:
                print(f"First Item Keys: {list(perf[0].keys())}")
                print(f"First Item Volume: {perf[0].get('volume')}")
                print(f"First Item TotalVol: {perf[0].get('total_volume')}")
            
            print(f"Price Trend Items: {len(content.get('avg_price_trend', []))}")
            print("SUCCESS! JSON Content loaded.")
        else:
            print("FAILED with status", response.status_code)
            
    except Exception as e:
        print(f"!!! CRASH in View: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_view()
