import os
import django
import sys
import json

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlp import QueryMatcher
from trade_data.models import ProductItem

def verify_fuzzy():
    print("--- Verifying Fuzzy Match for Typo Items ---")
    
    # 1. Identify Target Typo Item ID
    typo_name = "DEXTROSE MONOYDRATE"
    try:
        typo_item = ProductItem.objects.get(name__icontains=typo_name)
        print(f"Target Typo Item: {typo_item.name} (ID: {typo_item.id})")
    except ProductItem.DoesNotExist:
        print("Typo item not found in DB? Check audit.")
        return

    # 2. Run NLP Match with Correct Spelling
    query = "buy dextrose monohydrate"
    print(f"Query: '{query}'")
    
    matcher = QueryMatcher()
    matches = matcher.match(query)
    
    found = False
    for m in matches:
        variants = m.get('matched_variants', [])
        if typo_item.id in variants:
            found = True
            print(f"SUCCESS: Typo Item ID {typo_item.id} found in variants for {m['name']}!")
            break
            
    if not found:
        print("FAIL: Typo Item ID not found in matched variants.")
        for m in matches:
            print(f"Match: {m['name']} -> Variants: {m.get('matched_variants')}")

if __name__ == "__main__":
    verify_fuzzy()
