import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 717
seller = 'Seawall'

qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller)
print(f'Rows: {qs.count()}')
print(f'Distinct tx_ref: {len(set(qs.values_list("tx_reference", flat=True)))}')
print(f'Distinct tx_ref db: {qs.values("tx_reference").distinct().count()}')

sc_id = 745
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller)
print(f'745 Rows: {qs.count()}')
print(f'745 Distinct tx_ref: {qs.values("tx_reference").distinct().count()}')

sc_id = 827
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller)
print(f'827 Rows: {qs.count()}')
print(f'827 Distinct tx_ref: {qs.values("tx_reference").distinct().count()}')
