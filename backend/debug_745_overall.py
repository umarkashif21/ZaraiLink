import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 745
qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT')
print(f"Total rows for 745 overall: {qs.count()}")
print(f"Total rows for ANY seller on 745: {qs.values('seller').annotate(c=Count('id')).order_by('-c')}")
