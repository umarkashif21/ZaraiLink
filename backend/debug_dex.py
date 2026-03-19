import os, django, sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import ProductSubCategory, Transaction
from search.services.search_service import SearchService

# Test: simulate exactly what happens when user clicks "Dextrose Anhydrous" from "buyyy dex"
# Frontend would send: q=buyyy dex, hs_code=1702.3, variant_name=Dextrose Anhydrous, subcat_id=<some_id>

# First, find the actual subcat ID for Dextrose Anhydrous
scs = ProductSubCategory.objects.filter(hs_code='1702.3').order_by('name')
print("All subcats hs_code=1702.3:")
da_id = None
for sc in scs:
    import_tx = Transaction.objects.filter(product_item__sub_category_id=sc.id, trade_type='IMPORT').count()
    print(f"  id={sc.id}  name={repr(sc.name)}  import_tx={import_tx}")
    if sc.name == 'Dextrose Anhydrous':
        da_id = sc.id

print()
if da_id:
    print(f"Dextrose Anhydrous id={da_id}")
    # Simulate execute_search with subcat_id set
    svc = SearchService()
    result = svc.execute_search(
        raw_query='buyyy dex',
        ui_context='worldwide',
        subcat_id=da_id,
        variant_name='Dextrose Anhydrous'
    )
    print("needs_disambig:", result.get('needs_disambiguation'))
    print("profiles count:", len(result.get('profiles', [])))
    print("is_broad:", result.get('is_broad_search'))
else:
    print("Dextrose Anhydrous not found in hs_code=1702.3!")
