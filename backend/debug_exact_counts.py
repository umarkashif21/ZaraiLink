import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

print(f"Seawall 717 dist tx for Pakistan: {Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall', destination_country='Pakistan').values('tx_reference').distinct().count()}")
print(f"Seawall 717 dist tx overall: {Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall').values('tx_reference').distinct().count()}")

print(f"Seawall 745 dist tx overall: {Transaction.objects.filter(product_item__sub_category_id=745, trade_type='IMPORT', seller__icontains='Seawall').values('tx_reference').distinct().count()}")
print(f"Chuming 717 dist tx overall: {Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Chuming').values('tx_reference').distinct().count()}")
