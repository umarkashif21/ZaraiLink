import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

tx717 = set(Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall', tx_reference__isnull=False).values_list('tx_reference', flat=True))
tx745 = set(Transaction.objects.filter(product_item__sub_category_id=745, trade_type='IMPORT', seller__icontains='Seawall', tx_reference__isnull=False).values_list('tx_reference', flat=True))

overlap = tx717.intersection(tx745)
print(f"Overlap count: {len(overlap)}")
print("Sample of overlapping tx_references:")
for tx in list(overlap)[:10]:
    print(repr(tx))
