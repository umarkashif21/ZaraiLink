import os, sys, django
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductSubCategory, ProductItem

with open('subcat_vs_items.txt', 'w', encoding='utf-8') as f:
    f.write("=== SubCategory vs ProductItem Comparison ===\n\n")
    
    for sc in ProductSubCategory.objects.all().order_by('id'):
        items = ProductItem.objects.filter(sub_category=sc)
        item_names = list(items.values_list('name', flat=True).distinct()[:20])
        f.write(f"\nSubCategory [{sc.id}]: {sc.name} (HS: {sc.hs_code})\n")
        f.write(f"  Total ProductItems: {items.count()}\n")
        f.write(f"  Sample Item Names:\n")
        for name in item_names:
            f.write(f"    - {name}\n")

print("Written to subcat_vs_items.txt")
