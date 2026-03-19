import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

qs = Transaction.objects.filter(tx_reference='IMPORT-ROW-1215')
print(f"Total entries for 'IMPORT-ROW-1215': {qs.count()}")
for t in qs:
    print(f"ID: {t.id}, Source: {t.source_file}, Subcat: {t.product_item.sub_category_id}, Seller: {t.seller}, Date: {t.reporting_date}")
