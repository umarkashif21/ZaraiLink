import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction

# Check IMPORT data with China
print("====== IMPORT TRANSACTIONS FROM CHINA ======")
imports_from_china = Transaction.objects.filter(
    trade_type='IMPORT',
    origin_country='China'
)
print(f"Total IMPORT transactions from China: {imports_from_china.count()}")

if imports_from_china.exists():
    sample = imports_from_china.first()
    print(f"\nSample transaction:")
    print(f"  Trade Type: {sample.trade_type}")
    print(f"  Origin: {sample.origin_country}")
    print(f"  Destination: {sample.destination_country}")
    print(f"  Seller: {sample.seller}")
    print(f"  Product: {sample.product_item.sub_category.name if sample.product_item and sample.product_item.sub_category else 'N/A'}")

# Check for dextrose in subcategories
print("\n====== DEXTROSE SUBCATEGORIES ======")
from trade_data.models import ProductSubCategory
dextrose_subs = ProductSubCategory.objects.filter(name__icontains='dextrose')
print(f"Found {dextrose_subs.count()} subcategories with 'dextrose'")
if dextrose_subs.exists():
    for sub in dextrose_subs:
        print(f"  - ID: {sub.id}, Name: {sub.name}, HS: {sub.hs_code}")
        
        # Check if there are Chinese imports for this subcategory
        chinese_imports = Transaction.objects.filter(
            trade_type='IMPORT',
            origin_country='China',
            product_item__sub_category=sub
        )
        print(f"    Chinese imports: {chinese_imports.count()}")
