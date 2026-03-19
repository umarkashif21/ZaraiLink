import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction
from search.services.aggregation import SupplierAggregator

agg = SupplierAggregator()
results = agg.get_suppliers_for_subcategories(
    subcategory_ids=[717],  # Dextrose Anhydrous
    intent='BUY',
    scope='WORLDWIDE',
)

seawall = next((r for r in results if 'Seawall' in r['name']), None)
if seawall:
    print(f"Seawall Dextrose Anhydrous count in aggregator: {seawall.get('shipment_count')}")
else:
    print('Seawall not found for Dextrose Anhydrous')
