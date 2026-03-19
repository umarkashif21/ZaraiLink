import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction, ProductSubCategory
from django.db.models import Count

scs = ProductSubCategory.objects.filter(hs_code='1702.3')
for sc in scs:
    count = Transaction.objects.filter(product_item__sub_category_id=sc.id, trade_type='IMPORT', seller__icontains='Seawall').count()
    if count > 0:
        print(f'{sc.name} ({sc.id}): {count} Seawall txs')
