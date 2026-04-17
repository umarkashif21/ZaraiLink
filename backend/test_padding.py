import os, sys, django
sys.path.append(r'c:\Users\Dell\Documents\ZaraiLink\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductCategory, ProductSubCategory, ProductItem, Transaction

def normalize_to_8_digits(code):
    if not code:
        return code
    code_str = str(code).strip()
    if not code_str:
        return code_str
    
    parts = code_str.split('.')
    if len(parts) == 1:
        return f"{parts[0].zfill(4)}.0000"
    else:
        int_part = parts[0].zfill(4)
        dec_part = parts[1].ljust(4, '0')
        return f"{int_part}.{dec_part}"

print("Sample conversions:")
samples = ["1702.1", "1702.111", "0101.1", "1702", "1704.909"]
for s in samples:
    print(f"'{s}' -> '{normalize_to_8_digits(s)}'")

print("Updating Product tables...")
for model in [ProductCategory, ProductSubCategory]:
    count = 0
    for obj in model.objects.all():
        padded = normalize_to_8_digits(obj.hs_code)
        if obj.hs_code != padded:
            obj.hs_code = padded
            obj.save(update_fields=['hs_code'])
            count += 1
    print(f"Updated {count} records in {model.__name__}")

print("Updating Transactions...")
from django.db import transaction
updated_tx = 0
chunk_size = 50000

# Do it efficiently
tx_to_update = []
for tx in Transaction.objects.all().iterator(chunk_size=10000):
    padded = normalize_to_8_digits(tx.hs_code)
    if tx.hs_code != padded:
        tx.hs_code = padded
        tx_to_update.append(tx)
        
    if len(tx_to_update) >= chunk_size:
        with transaction.atomic():
            Transaction.objects.bulk_update(tx_to_update, ['hs_code'])
        updated_tx += len(tx_to_update)
        print(f"  ...updated {updated_tx} transactions")
        tx_to_update = []

if tx_to_update:
    with transaction.atomic():
        Transaction.objects.bulk_update(tx_to_update, ['hs_code'])
    updated_tx += len(tx_to_update)

print(f"Total Transactions Updated: {updated_tx}")
print("Database Padding Complete!")

