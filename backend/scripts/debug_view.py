import os
import sys
import json
import django
from django.conf import settings
from django.http import HttpRequest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.views import company_products_api, company_trends_api

COMPANY = "Abbott Laboratories Pakistan Ltd"

request = HttpRequest()
request.method = 'GET'
request.GET['direction'] = 'import'
request.META['SERVER_NAME'] = 'testserver'
request.META['SERVER_PORT'] = '80'

print(f"DEBUGGING VIEW for: {COMPANY}")


response = company_products_api(request, COMPANY)
print(f"Products Status: {response.status_code}")
if response.status_code == 200:
    content = json.loads(response.content)
    if 'product_performance' in content and content['product_performance']:
        top = content['product_performance'][0]
        print("--- Product Performance [0] ---")
        print(f"Product: {top.get('product_name')}")
        print(f"Subcat: '{top.get('subcat')}'")
        print(f"Category Name: '{top.get('category_name')}'")
        print(f"YoY Growth (Raw): {top.get('yoy_growth')}")
    else:
        print("No product_performance found.")


response_trends = company_trends_api(request, COMPANY)
print(f"Trends Status: {response_trends.status_code}")
if response_trends.status_code == 200:
    content = json.loads(response_trends.content)
    if 'volume_price_trend' in content and content['volume_price_trend']:
         last = content['volume_price_trend'][-1]
         print("--- Trends (Last Month) ---")
         print(f"Month: {last.get('month')}")
         print(f"Product Name: '{last.get('product_name')}'")
         print(f"YoY Vol Growth: {last.get('yoy_volume_growth')}")
    else:
         print("No trends found.")
