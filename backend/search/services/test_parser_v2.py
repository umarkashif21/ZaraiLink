import sys
import os
import django
import json
import re

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.query_parser import QueryInterpreter

def run_tests():
    parser = QueryInterpreter()
    
    # Test Cases based on User Feedback
    test_cases = [
        # 1. Intent Ambiguity
        {
            "query": "I want to buy from an exporter",
            "expected": {"intent": "BUY"}
        },
        {
            "query": "Find sellers in China", # "sellers" -> BUY (context: who sells?)
            "expected": {"intent": "BUY"}
        },
        
        # 2. Multi-Intent False Positives
        {
            "query": "Buy sugar in China and India",
            "expected": {
                "multi_intent": False,
                "country_filter": ["China", "India"] # Should extract both, no split
            }
        },
        
        # 3. Country Normalization / Misspellings
        {
            "query": "Rice suppliers in Pakistaan",
            "expected": {"country_filter": ["Pakistan"]}
        },
        {
            "query": "Demand in U.S.",
            "expected": {"country_filter": ["USA"]}
        },
        
        # 4. Price Extraction
        {
            "query": "Sugar under 500 EUR", # Currency support
            "expected": {"product": "sugar", "price_ceiling": 500.0} # We might need to store currency, but for now check extraction
        },
        
        # 5. Time Extraction
        {
            "query": "Iron ore prices Q1 2025",
            "expected": {"time_range": "Q1 2025"}
        },
        
        # 6. Counterparty Extraction & Stopwords
        {
            "query": "Company X sugar",
            "expected": {"product": "sugar", "counterparty_name": "Company X"} # Heuristic check
        },
        {
            "query": "Iron Ore prices",
            "expected": {"product": "iron ore"} # "Ore" shouldn't be removed or "Iron" shouldn't be valid alone if "Ore" is part of it
        }
    ]
    
    results = []
    failed = 0
    
    print("Running Refined Parser Tests (v2)...")
    
    for case in test_cases:
        query = case['query']
        expected = case['expected']
        print(f"\nTesting: '{query}'")
        
        try:
            got = parser.parse(query)
        except Exception as e:
            print(f"  ERROR: Exception during parse: {e}")
            failed += 1
            results.append({"query": query, "status": "ERROR", "error": str(e)})
            continue

        is_pass = True
        failed_keys = []
        
        for key, val in expected.items():
            if key == "country_filter":
                # Check set equality for lists
                if set(got.get(key, [])) != set(val):
                     is_pass = False
                     failed_keys.append(key)
            elif got.get(key) != val:
                is_pass = False
                failed_keys.append(key)
        
        if is_pass:
            print("  PASS")
            results.append({"query": query, "status": "PASS"})
        else:
            print("  FAIL")
            print(f"    Expected: {expected}")
            print(f"    Got:      {json.dumps(got, indent=2)}")
            failed += 1
            results.append({
                "query": query,
                "status": "FAIL",
                "expected": expected,
                "got": got
            })
            
    print(f"\nTotal Failed: {failed} / {len(test_cases)}")
    
    with open("search/services/test_results_v2.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_tests()
