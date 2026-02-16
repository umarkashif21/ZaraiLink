import os
import django
import sys
from django.db.models import Count

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductSubCategory, ProductItem, Transaction

def check_dextrose_data():
    print("--- Checking Data for Dextrose Items ---")
    subcats = ProductSubCategory.objects.filter(name__icontains='dextrose')
    for sc in subcats:
        print(f"SubCategory: {sc.name} (ID: {sc.id})")
        
        items = ProductItem.objects.filter(sub_category=sc)
        for item in items:
            tx_count = Transaction.objects.filter(product_item=item).count()
            print(f"  Item: {item.name} (ID: {item.id}) -> {tx_count} Transactions")
            
        # Check transactions with just subcategory but NO item (if any)
        null_item_count = Transaction.objects.filter(product_item__sub_category=sc, product_item__isnull=True).count()
        print(f"  Transactions with SubCat {sc.id} but NULL Item: {null_item_count}")

if __name__ == "__main__":
    check_dextrose_data()
