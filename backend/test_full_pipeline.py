import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, ProductSubCategory
from search.services.nlp import QueryMatcher

# Test the full pipeline
print("====== FULL PIPELINE TEST ======")
matcher = QueryMatcher()
matches = matcher.match("dextrose")
print(f"\nNLP matched {len(matches)} subcategories for 'dextrose'")

if matches:
    subcategory_ids = [m['id'] for m in matches[:5]]  # Top 5
    print(f"Top subcategory IDs: {subcategory_ids}")
    
    for sub_id in subcategory_ids:
        sub = ProductSubCategory.objects.get(id=sub_id)
        print(f"\nSubcategory {sub_id}: {sub.name}")
        
        # Step 1: IMPORTs for this subcategory
        imports = Transaction.objects.filter(
            trade_type='IMPORT',
            product_item__sub_category_id=sub_id
        )
        print(f"  Total IMPORT transactions: {imports.count()}")
        
        # Step 2: IMPORTs from China for this subcategory
        imports_china = imports.filter(origin_country='China')
        print(f"  IMPORT from China: {imports_china.count()}")
        
        if imports_china.exists():
            sample = imports_china.first()
            print(f"  Sample: {sample.seller} - {sample.origin_country}")
