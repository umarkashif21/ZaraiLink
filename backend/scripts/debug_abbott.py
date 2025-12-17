import os
import sys
import django
from datetime import date
from django.db import models
from django.db.models import Min, Max, Sum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, ProductItem
from trade_ledger.services.products import get_company_product_performance
from trade_ledger.services.trends import get_volume_price_monthly

COMPANY = "Abbott Laboratories Pakistan Ltd"

print(f"DEBUGGING COMPANY: {COMPANY}")


qs = Transaction.objects.filter(buyer=COMPANY)
agg = qs.aggregate(min_date=Min('reporting_date'), max_date=Max('reporting_date'), count=models.Count('id'))
print(f"Date Range (Import): {agg['min_date']} to {agg['max_date']} (Count: {agg['count']})")

if not agg['count']:
    print("Trying Export...")
    qs = Transaction.objects.filter(seller=COMPANY)
    agg = qs.aggregate(min_date=Min('reporting_date'), max_date=Max('reporting_date'), count=models.Count('id'))
    print(f"Date Range (Export): {agg['min_date']} to {agg['max_date']} (Count: {agg['count']})")


prods = get_company_product_performance(COMPANY, direction='import')
if not prods:
     prods = get_company_product_performance(COMPANY, direction='export')
     print("Switched to Export for Products test")

if prods:
    top = prods[0]
    print(f"Top Product: {top['product_name']}")
    print(f"Subcat Value: '{top.get('subcat')}'")
    print(f"YoY Growth Value: {top.get('yoy_growth')}")
else:
    print("No products found.")


trends = get_volume_price_monthly(COMPANY, direction='import')
if not trends:
    trends = get_volume_price_monthly(COMPANY, direction='export')

if trends:
    last = trends[-1]
    print(f"Last Trend Month: {last['month']}")
    print(f"Trend Keys: {list(last.keys())}")
    print(f"Trend YoY Vol: {last.get('yoy_volume_growth')}")
else:
    print("No trends found.")
