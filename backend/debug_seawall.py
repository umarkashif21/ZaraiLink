from search.services.nlp import QueryMatcher
from search.services.aggregation import SupplierAggregator
from trade_data.models import Transaction, ProductSubCategory

def debug_seawall():
    query = "dextrose anhydrous"
    seller = "Seawall Enterprise Ltd" # Exact name from user report might be slightly different, check 'Seawall Enterprise Limited' vs 'Ltd'
    
    print(f"--- Debugging '{seller}' for query '{query}' ---")
    
    # 1. NLP Matches
    matcher = QueryMatcher()
    matches = matcher.match(query)
    print(f"\nNLP Matches ({len(matches)}):")
    for m in matches:
        print(f" - {m['id']}: {m['name']} (Score: {m['score']})")
    
    matched_ids = [m['id'] for m in matches]
    
    # 2. Transaction Counts per SubCategory
    print("\nTransaction Counts by SubCategory for Seawall:")
    total = 0
    for m in matches:
        count = Transaction.objects.filter(
            seller__icontains="Seawall", # fuzzy match to be safe
            product_item__sub_category_id=m['id']
        ).count()
        print(f" - {m['name']} (ID {m['id']}): {count}")
        total += count
        
    print(f"\nTotal Calculated: {total}")

debug_seawall()
