import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction
from django.db.models import Count

sc_id = 717
seller = 'Chuming'

qs = Transaction.objects.filter(product_item__sub_category_id=sc_id, trade_type='IMPORT', seller__icontains=seller, destination_country='Pakistan')
res = qs.aggregate(
    count=Count('id'),
    dist_date=Count('reporting_date', distinct=True),
    dist_tx=Count('tx_reference', distinct=True)
)
print(f"Chuming 717: rows={res['count']}, dist_date={res['dist_date']}, dist_tx={res['dist_tx']}")

seller = 'Qiqihar'
sqs = Transaction.objects.filter(product_item__sub_category_id=745, trade_type='IMPORT', seller__icontains=seller, destination_country='Pakistan')
res_sqs = sqs.aggregate(
    count=Count('id'),
    dist_date=Count('reporting_date', distinct=True),
    dist_tx=Count('tx_reference', distinct=True)
)
print(f"Qiqihar 745: rows={res_sqs['count']}, dist_date={res_sqs['dist_date']}, dist_tx={res_sqs['dist_tx']}")
