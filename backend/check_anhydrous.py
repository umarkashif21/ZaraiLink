import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductItem, Transaction

if __name__ == "__main__":
    print("--- Listing ALL items containing 'Dextrose Anhydrous' ---")
    items = ProductItem.objects.filter(name__icontains="Dextrose Anhydrous").select_related('sub_category')
    for i in items:
        c = Transaction.objects.filter(product_item=i).count()
        print(f"Item: {i.name} (ID: {i.id}) -> Parent: {i.sub_category.name} (ID: {i.sub_category.id}) -> Count: {c}")
