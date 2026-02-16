import os, sys, django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Product, ProductCategory, ProductSubCategory, ProductItem, Transaction

# Write output to a UTF-8 file to avoid PowerShell encoding issues
with open('audit_result.txt', 'w', encoding='utf-8') as f:
    f.write("=== PRODUCT HIERARCHY AUDIT ===\n\n")
    f.write(f"Products (top-level HS2):   {Product.objects.count()}\n")
    f.write(f"ProductCategories (HS4):    {ProductCategory.objects.count()}\n")
    f.write(f"ProductSubCategories (HS6): {ProductSubCategory.objects.count()}\n")
    f.write(f"ProductItems (leaf names):  {ProductItem.objects.count()}\n")
    f.write(f"\nTransactions Total:         {Transaction.objects.count()}\n")
    f.write(f"  IMPORT:                   {Transaction.objects.filter(trade_type='IMPORT').count()}\n")
    f.write(f"  EXPORT:                   {Transaction.objects.filter(trade_type='EXPORT').count()}\n")
    
    items_with_tx = Transaction.objects.exclude(product_item__isnull=True).values_list('product_item_id', flat=True).distinct().count()
    f.write(f"\nProductItems with transactions: {items_with_tx}\n")
    
    subcats_with_tx = (
        Transaction.objects
        .exclude(product_item__isnull=True)
        .values_list('product_item__sub_category_id', flat=True)
        .distinct()
        .count()
    )
    f.write(f"SubCategories with transactions: {subcats_with_tx}\n")
    
    f.write("\n--- All SubCategories ---\n")
    for sc in ProductSubCategory.objects.select_related('category', 'category__product').all():
        tx_count = Transaction.objects.filter(product_item__sub_category=sc).count()
        f.write(f"  [{sc.id}] {sc.name} (HS:{sc.hs_code}) | Cat: {sc.category.name} | Txns: {tx_count}\n")

    f.write(f"\n--- Total ProductItems: {ProductItem.objects.count()} ---\n")
    f.write("(Each ProductItem is a specific item name like 'DEXTROSE MONOHYDRATE', 'CHOCOLATE BAR', etc.)\n")
    f.write("(Each SubCategory groups related items, e.g. 'Dextrose Anhydrous' groups all dextrose variants)\n")

print("Audit written to audit_result.txt")
