import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 717
seller = 'Seawall'
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller, tx_reference__isnull=False)
print(f"Total rows for Seawall 717: {qs.count()}")
print(f"Distinct tx_ref for Seawall 717: {qs.values('tx_reference').distinct().count()}")

sc_id = 745
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller, tx_reference__isnull=False)
print(f"Total rows for Seawall 745: {qs.count()}")
print(f"Distinct tx_ref for Seawall 745: {qs.values('tx_reference').distinct().count()}")
