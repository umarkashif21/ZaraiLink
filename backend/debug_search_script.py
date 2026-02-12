from search.services.nlp import QueryMatcher
from search.services.aggregation import SupplierAggregator
from trade_data.models import Transaction, ProductSubCategory

def debug():
    q = "dextrose"
    print(f"\n--- Debugging Query: '{q}' ---")
    
    # 1. NLP
    matcher = QueryMatcher()
    matches = matcher.match(q)
    print(f"NLP Matches: {len(matches)}")
    for m in matches:
        print(f" - {m['name']} (ID: {m['id']}, Score: {m['score']})")

    if not matches:
        print("NO MATCHES FOUND. Check data or index.")
        return

    ids = [m['id'] for m in matches]
    
    # 2. Aggregator
    aggregator = SupplierAggregator()
    suppliers = aggregator.get_suppliers_for_subcategories(ids)
    print(f"\nSuppliers Found: {len(suppliers)}")
    
    # 3. Data Check
    print("\n--- Data Check ---")
    total_tx = Transaction.objects.filter(product_item__sub_category_id__in=ids).count()
    print(f"Total Transactions for these IDs: {total_tx}")
    
    import_tx = Transaction.objects.filter(product_item__sub_category_id__in=ids, trade_type='IMPORT').count()
    print(f"IMPORT Transactions: {import_tx}")
    
    export_tx = Transaction.objects.filter(product_item__sub_category_id__in=ids, trade_type='EXPORT').count()
    print(f"EXPORT Transactions: {export_tx}")
    
    if total_tx > 0:
        sample = Transaction.objects.filter(product_item__sub_category_id__in=ids).values('trade_type', 'seller').first()
        print(f"Sample Transaction: {sample}")

debug()
