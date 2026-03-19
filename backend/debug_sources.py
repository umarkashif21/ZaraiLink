import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 717
seller = 'Seawall'
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller)
for row in qs.values('source_file').annotate(c=Count('id')):
    print(f"{row['source_file']}: {row['c']}")
