import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from trade_data.models import Transaction
from collections import defaultdict

print("=== EXPLORER DEBUG ===")
total = Transaction.objects.count()
print(f"Total transactions in DB: {total}")

if total == 0:
    print("ERROR: No transactions in DB!")
    sys.exit(1)

# Show sample transaction
sample = Transaction.objects.values('buyer', 'seller', 'qty_mt', 'usd', 'country', 'reporting_date').first()
print(f"Sample transaction: {sample}")

# Test direction=both path
base_qs = Transaction.objects.all()
company_stats = defaultdict(lambda: {
    'total_volume': 0, 'total_value': 0,
    'transaction_count': 0, 'active_partners': set(),
    'first_trade': None, 'last_trade': None
})

processed = 0
for tx in base_qs.values('buyer', 'seller', 'qty_mt', 'usd', 'usd_per_mt', 'reporting_date'):
    for role in ['buyer', 'seller']:
        name = tx[role]
        if name and name.lower() != 'unknown':
            cs = company_stats[name]
            cs['total_volume'] += float(tx['qty_mt'] or 0)
            cs['total_value'] += float(tx['usd'] or 0)
            cs['transaction_count'] += 1
            other = tx['seller' if role == 'buyer' else 'buyer']
            if other:
                cs['active_partners'].add(other)
            if cs['first_trade'] is None or tx['reporting_date'] < cs['first_trade']:
                cs['first_trade'] = tx['reporting_date']
            if cs['last_trade'] is None or tx['reporting_date'] > cs['last_trade']:
                cs['last_trade'] = tx['reporting_date']
            processed += 1

print(f"\nProcessed {processed} role-entries")
print(f"Unique companies found: {len(company_stats)}")

if company_stats:
    print("\nTop 5 companies by volume:")
    sorted_comps = sorted(company_stats.items(), key=lambda x: x[1]['total_volume'], reverse=True)
    for name, stats in sorted_comps[:5]:
        print(f"  {name}: vol={stats['total_volume']:.2f}, txns={stats['transaction_count']}")
else:
    print("ERROR: No companies found!")

# Check what direction='both' returns via the actual service
print("\n=== Testing actual explorer service ===")
from trade_ledger.services.explorer import get_explorer_companies
try:
    result = get_explorer_companies(direction='both', limit=5)
    print(f"Service returned {len(result)} companies")
    if result:
        print(f"First result: {result[0]}")
    else:
        print("ERROR: Service returned empty list!")
except Exception as e:
    import traceback
    print(f"Exception in service: {e}")
    traceback.print_exc()
