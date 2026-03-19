import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from trade_data.models import Transaction

print("Seawall 717 rows:")
for t in Transaction.objects.filter(seller__icontains='Seawall', product_item__sub_category_id=717)[:5]:
    print(f"Name: {t.product_item.name}, ID: {t.id}, Qty: {t.qty_mt}, Ref: {t.tx_reference}")

print("\nSeawall 745 rows:")
for t in Transaction.objects.filter(seller__icontains='Seawall', product_item__sub_category_id=745)[:5]:
    print(f"Name: {t.product_item.name}, ID: {t.id}, Qty: {t.qty_mt}, Ref: {t.tx_reference}")
