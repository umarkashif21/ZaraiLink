import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

print("Top 10 Seawall 717 rows:")
for t in Transaction.objects.filter(seller__icontains='Seawall', product_item__sub_category_id=717)[:10]:
    print(f"Name: {t.product_item.product_name}, ID: {t.id}, Qty: {t.qty_mt}")

print("\nTop 10 Seawall 745 rows:")
for t in Transaction.objects.filter(seller__icontains='Seawall', product_item__sub_category_id=745)[:10]:
    print(f"Name: {t.product_item.product_name}, ID: {t.id}, Qty: {t.qty_mt}")
