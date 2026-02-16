import os
import django
import sys
import json

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlp import QueryMatcher
from search.services.aggregation import SupplierAggregator
from trade_data.models import ProductSubCategory, ProductItem

def test_dextrose_search():
    print("\n=== TEST 1: Generic Search 'buy dextrose' ===")
    matcher = QueryMatcher()
    matches = matcher.match("buy dextrose")
    
    print(f"Matches found: {len(matches)}")
    for m in matches:
        print(f"  - {m['name']} (Score: {m['score']}, Variant: {m.get('matched_variant')})")
        
    if matches:
        top_match = matches[0]
        # Simulate Aggregation
        agg = SupplierAggregator()
        results = agg.get_suppliers_for_subcategories([top_match['id']])
        print(f"  > Aggregated Results (Generic): {len(results)} suppliers")
        
        # Check available variants (Sidebar logic)
        items = ProductItem.objects.filter(sub_category_id=top_match['id'])
        print(f"  > Available Variants in Sidebar: {items.count()}")
        for i in items[:3]:
            print(f"    - {i.name} (ID: {i.id})")

def test_specific_search():
    print("\n=== TEST 2: Specific Search 'buy dextrose anhydrous' ===")
    matcher = QueryMatcher()
    matches = matcher.match("buy dextrose anhydrous")
    
    print(f"Matches found: {len(matches)}")
    matched_variant_ids = []
    
    for m in matches:
        print(f"  - {m['name']} (Score: {m['score']}, Matched Variants: {m.get('matched_variants')})")
        if m.get('matched_variants'):
            matched_variant_ids = m.get('matched_variants')
            print(f"    -> DETECTED VARIANTS: {m.get('variant_name')} (IDs: {matched_variant_ids})")

    if matched_variant_ids:
        print("\n  > Applying Auto-Filter for Variants...")
        agg = SupplierAggregator()
        # Pass the variant IDs to the aggregator
        results = agg.get_suppliers_for_subcategories(
            [matches[0]['id']], 
            product_item_filter=matched_variant_ids
        )
        print(f"  > Aggregated Results (Filtered): {len(results)} suppliers")
        if len(results) > 0:
            print(f"    - Top Supplier: {results[0]['name']} (Vol: {results[0]['total_volume']})")
    else:
        print("FAIL: Did not detect matched_variants")

if __name__ == "__main__":
    test_dextrose_search()
    test_specific_search()
