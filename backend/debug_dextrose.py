import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductSubCategory, ProductItem

def check_dextrose():
    print("--- Checking ProductSubCategory for 'Dextrose' ---")
    subcats = ProductSubCategory.objects.filter(name__icontains='dextrose')
    for sc in subcats:
        print(f"SubCategory: {sc.name} (ID: {sc.id}, HS: {sc.hs_code})")
        
        print(f"  > Items under {sc.name}:")
        items = ProductItem.objects.filter(sub_category=sc)
        for item in items:
            print(f"    - Item: {item.name} (ID: {item.id})")

    print("\n--- Checking ProductItem for 'Dextrose Anhydrous' ---")
    items = ProductItem.objects.filter(name__icontains='dextrose anhydrous')
    for item in items:
        print(f"Item Match: {item.name} -> Parent SubCategory: {item.sub_category.name} (ID: {item.sub_category.id})")

if __name__ == "__main__":
    check_dextrose()
