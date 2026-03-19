import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 717
seller = 'Seawall'

print(f"Total rows for Seawall (717): {Transaction.objects.filter(product_item__sub_category_id=sc_id, seller__icontains=seller).count()}")
print(f"Total EXPORT rows for Seawall (717): {Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='EXPORT', seller__icontains=seller).count()}")
print(f"Total IMPORT rows for Seawall (717): {Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller).count()}")

print("Let's group by destination_country for IMPORT:")
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller)
for row in qs.values('destination_country').annotate(count=Count('id'), dist_date=Count('reporting_date', distinct=True), dist_tx=Count('tx_reference', distinct=True)):
    print(row)
