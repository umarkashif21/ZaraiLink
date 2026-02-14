import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlp import QueryMatcher
from search.services.aggregation import SupplierAggregator
from trade_data.models import Transaction

# Test NLP matching
print("====== NLP MATCHING ======")
matcher = QueryMatcher()
matches = matcher.match("dextrose")
print(f"Matched subcategories: {len(matches)}")
if matches:
    print(f"Top match: {matches[0]}")
    subcategory_ids = [m['id'] for m in matches]
    print(f"Subcategory IDs: {subcategory_ids}")
    
    # Test database query
    print("\n====== DATABASE QUERY ======")
    print("Query: EXPORT + origin_country=China + subcategories")
    
    queryset = Transaction.objects.filter(
        product_item__sub_category_id__in=subcategory_ids,
        trade_type='EXPORT',
        origin_country='China'
    )
    
    count = queryset.count()
    print(f"Total matching transactions: {count}")
    
    if count > 0:
        # Show sample
        sample = queryset.first()
        print(f"\nSample transaction:")
        print(f"  Seller: {sample.seller}")
        print(f"  Trade Type: {sample.trade_type}")
        print(f"  Origin: {sample.origin_country}")
        print(f"  Destination: {sample.destination_country}")
        print(f"  Product: {sample.product_item.sub_category.name if sample.product_item and sample.product_item.sub_category else 'N/A'}")
    
    # Test aggregation
    print("\n====== AGGREGATION TEST ======")
    aggregator = SupplierAggregator()
    results = aggregator.get_suppliers_for_subcategories(
        subcategory_ids,
        intent='BUY',
        scope='WORLDWIDE',
        country_filter=['China']
    )
    print(f"Aggregated suppliers: {len(results)}")
    if results:
        print(f"First supplier: {results[0].get('name')}")
else:
    print("No matches found for 'dextrose'")
