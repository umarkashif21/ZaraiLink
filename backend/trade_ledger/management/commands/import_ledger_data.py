import pandas as pd
from django.core.management.base import BaseCommand
from trade_data.models import Transaction, ProductItem, ProductSubCategory, ProductCategory, Product
from django.db import transaction
from datetime import datetime
import os
import uuid

class Command(BaseCommand):
    help = 'Import transactions from Excel file with option to wipe existing data'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')
        parser.add_argument('--wipe', action='store_true', help='Wipe existing data before import')

    def handle(self, *args, **options):
        file_path = options['file_path']
        wipe = options['wipe']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        if wipe:
            self.stdout.write(self.style.WARNING("Wiping existing transactions..."))
            Transaction.objects.all().delete()
            
            
            
            self.stdout.write(self.style.SUCCESS(f"Deleted existing transactions"))
        
        self.stdout.write(f"Reading {file_path}...")
        try:
            df = pd.read_excel(file_path, header=6)
            df.columns = df.columns.astype(str).str.strip()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel: {e}"))
            return

        
        root_product, _ = Product.objects.get_or_create(
            name="General Trade",
            defaults={"hs_code": "000000"}
        )

        records_to_create = []
        product_item_cache = {}
        
        self.stdout.write("Processing rows...")
        
        for index, row in df.iterrows():
            try:
                raw_date = row.get('Date')
                if pd.isna(raw_date):
                    continue
                
                if isinstance(raw_date, (int, float)):
                    date_val = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(raw_date) - 2).date()
                else:
                    date_val = pd.to_datetime(raw_date).date()

                cat_name = str(row.get('Category', 'Uncategorized')).strip()
                sub_name = str(row.get('Sub-Category', 'General')).strip()
                item_name = str(row.get('Item Description', 'Unknown Item')).strip()
                hs_code_tx = str(row.get('HS Code', '')).strip()

                cache_key = (cat_name, sub_name, item_name)
                
                if cache_key not in product_item_cache:
                    
                    category = ProductCategory.objects.filter(name=cat_name).first()
                    if not category:
                        category = ProductCategory.objects.create(
                            name=cat_name,
                            product=root_product,
                            hs_code=uuid.uuid4().hex[:10]
                        )
                    
                    
                    sub_cat = ProductSubCategory.objects.filter(name=sub_name, category=category).first()
                    if not sub_cat:
                        sub_cat = ProductSubCategory.objects.create(
                            name=sub_name,
                            category=category,
                            hs_code=uuid.uuid4().hex[:10]
                        )
                    
                    
                    item = ProductItem.objects.filter(name=item_name, sub_category=sub_cat).first()
                    if not item:
                        item = ProductItem.objects.create(
                            name=item_name,
                            sub_category=sub_cat
                        )
                    
                    product_item_cache[cache_key] = item
                
                p_item = product_item_cache[cache_key]

                qty_kg = pd.to_numeric(row.get('Qty KG'), errors='coerce') or 0
                qty_mt = pd.to_numeric(row.get('Qty MT'), errors='coerce') or 0
                usd_kg = pd.to_numeric(row.get('USD/KG'), errors='coerce') or 0
                usd_mt = pd.to_numeric(row.get('USD/MT'), errors='coerce') or 0
                pkr_val = pd.to_numeric(row.get('PKR'), errors='coerce') or 0
                usd_val = pd.to_numeric(row.get('USD'), errors='coerce') or 0

                tx = Transaction(
                    source_file=os.path.basename(file_path),
                    tx_reference=f"ROW-{index}",
                    reporting_date=date_val,
                    hs_code=hs_code_tx,
                    product_item=p_item,
                    buyer=str(row.get('Buyer', '')).strip(),
                    seller=str(row.get('Seller', '')).strip(),
                    shipping_agent=str(row.get('Shipping Agents', '')).strip(),
                    country=str(row.get('Country', '')).strip(),
                    qty_kg=qty_kg,
                    qty_mt=qty_mt,
                    usd_per_kg=usd_kg,
                    usd_per_mt=usd_mt,
                    pkr=pkr_val,
                    usd=usd_val,
                    trade_type='import',
                    std_unit='MT'
                )
                records_to_create.append(tx)
                
                if len(records_to_create) >= 2000:
                    Transaction.objects.bulk_create(records_to_create)
                    records_to_create = []
                    self.stdout.write(f"Processed {index} rows...")

            except Exception as e:
                pass

        if records_to_create:
            Transaction.objects.bulk_create(records_to_create)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {Transaction.objects.count()} transactions."))
