import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

tx717 = set(Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall', tx_reference__isnull=False).values_list('tx_reference', flat=True))
tx745 = set(Transaction.objects.filter(product_item__sub_category_id=745, trade_type='IMPORT', seller__icontains='Seawall', tx_reference__isnull=False).values_list('tx_reference', flat=True))
txall = set(Transaction.objects.filter(trade_type='IMPORT', seller__icontains='Seawall').values_list('tx_reference', flat=True))

print(f"Total Unique tx total across all items: {len(txall)}")
print(f"Unique tx in 717: {len(tx717)}")
print(f"Unique tx in 745: {len(tx745)}")
print(f"Intersection (in both): {len(tx717.intersection(tx745))}")
print(f"Exclusive to 717: {len(tx717 - tx745)}")
