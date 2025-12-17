import os
import sys
import django
import json
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, Product, ProductCategory, ProductSubCategory, ProductItem
from django.db import transaction as db_transaction

BACKUP_FILE = 'transactions_backup_20251216_180840.json'

def restore_data():
    print(f"Reading {BACKUP_FILE}...")
    try:
        with open(BACKUP_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Backup file not found!")
        return

    print(f"Found {len(data)} transactions.")

    
    product_ids = set()
    for tx in data:
        pid = tx.get('product_item_id')
        if pid:
            product_ids.add(int(pid))
    
    print(f"Found {len(product_ids)} unique product items referenced.")

    
    with db_transaction.atomic():
        
        try:
            prod, _ = Product.objects.get_or_create(
                hs_code="00",
                defaults={"name": "Restored Product Base"}
            )
            cat, _ = ProductCategory.objects.get_or_create(
                hs_code="00.00",
                defaults={"name": "Restored Category", "product": prod}
            )
            subcat, _ = ProductSubCategory.objects.get_or_create(
                hs_code="0000.0000",
                defaults={"name": "Restored SubCategory", "category": cat}
            )
        except Exception as e:
            print(f"Error creating base hierarchy: {e}")
            return

        
        print("Restoring ProductItems...")
        created_count = 0
        existing_count = 0
        for pid in product_ids:
            if not ProductItem.objects.filter(id=pid).exists():
                ProductItem.objects.create(
                    id=pid,
                    name=f"Restored Item {pid}",
                    sub_category=subcat
                )
                created_count += 1
            else:
                existing_count += 1
        
        print(f"ProductItems: {created_count} created, {existing_count} existing.")

        
        print("Re-importing transactions with links...")
        
        
        
        
        
        
        Transaction.objects.all().delete()
        print("Cleared existing transactions.")

        tx_created = 0
        for item in data:
            try:
                
                pid = item.get('product_item_id')
                product_item = ProductItem.objects.get(id=int(pid)) if pid else None

                Transaction.objects.create(
                    source_file=item.get('source_file', 'backup'),
                    tx_reference=item.get('tx_reference', ''),
                    reporting_date=item.get('reporting_date'),
                    hs_code=item.get('hs_code', ''),
                    product_item=product_item,
                    buyer=item.get('buyer'),
                    seller=item.get('seller'),
                    shipping_agent=item.get('shipping_agent', ''),
                    country=item.get('country'),
                    qty_kg=item.get('qty_kg') or 0,
                    qty_mt=item.get('qty_mt') or 0,
                    usd_per_kg=item.get('usd_per_kg'),
                    usd_per_mt=item.get('usd_per_mt'),
                    pkr=item.get('pkr'),
                    usd=item.get('usd'),
                    trade_type=item.get('trade_type', 'import'),
                    std_unit=item.get('std_unit', 'MT')
                )
                tx_created += 1
            except Exception as e:
                print(f"Error importing tx: {e}")
        
        print(f"Successfully imported {tx_created} transactions.")

if __name__ == "__main__":
    restore_data()
