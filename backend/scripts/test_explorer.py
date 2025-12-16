import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.services.explorer import get_explorer_companies

print("Testing direction=both...")
result = get_explorer_companies(direction='both', limit=5)
print(f"Got {len(result)} companies")
if result:
    print(f"First company: {result[0]['company']}, Volume: {result[0]['total_volume']}")
else:
    print("No results")
