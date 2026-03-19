import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

qs = Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall', destination_country='Pakistan')
print(f'Distinct tx_reference for Pakistan: {qs.values("tx_reference").distinct().count()}')
print(f'Distinct reporting_date for Pakistan: {qs.values("reporting_date").distinct().count()}')
print(f'Total rows for Pakistan: {qs.count()}')

qs_all = Transaction.objects.filter(product_item__sub_category_id=717, trade_type='IMPORT', seller__icontains='Seawall')
print(f'\nDistinct tx_reference overall: {qs_all.values("tx_reference").distinct().count()}')
print(f'Distinct reporting_date overall: {qs_all.values("reporting_date").distinct().count()}')
print(f'Total rows overall: {qs_all.count()}')
