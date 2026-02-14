import sys
import os
import json

# Add backend to path to import QueryInterpreter
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from search.services.query_parser import QueryInterpreter

def run_tests():
    parser = QueryInterpreter()
    
    test_cases = [
        # BUY Families
        ("Who sells dextrose?", {"intent": "BUY", "family": 1, "product": "dextrose"}),
        ("Suppliers of sugar", {"intent": "BUY", "family": 1, "product": "sugar"}),
        ("Dextrose suppliers in China", {"intent": "BUY", "family": 2, "country_filter": ["China"], "product": "dextrose"}),
        ("Buy 50MT sugar from Brazil", {"intent": "BUY", "family": 3, "volume_mt": 50.0, "country_filter": ["Brazil"]}),
        
        ("Buy sugar under $500", {"intent": "BUY", "family": 4, "price_ceiling": 500.0, "product": "sugar"}),
        ("Suppliers active last 6 months", {"intent": "BUY", "family": 5, "time_range": "last 6 months"}),
        
        ("Top 3 suppliers for sugar", {"intent": "BUY", "family": 6}),
        ("Cheapest sugar suppliers", {"intent": "BUY", "family": 7}),
        ("Show recent shipments of sugar", {"intent": "BUY", "family": 8}),

        # SELL Families
        ("Who buys ethanol?", {"intent": "SELL", "family": 1, "product": "ethanol"}),
        ("Demand for wheat in UAE", {"intent": "SELL", "family": 2, "country_filter": ["UAE"], "product": "wheat"}),
        
        # Multi-Intent
        ("Find suppliers in China and buyers in Pakistan", {
            "family": 9, 
            "multi_intent": True
        }),
    ]
    
    results = []
    failed = 0
    for query, expected in test_cases:
        print(f"Testing: '{query}'")
        result = parser.parse(query)
        
        is_pass = True
        failed_keys = []
        for key, val in expected.items():
            if key == "country_filter":
                if set(result.get(key, [])) != set(val):
                     is_pass = False
                     failed_keys.append(key)
            elif key == "sub_intents":
                 if len(result.get(key, [])) != len(val):
                     is_pass = False
                     failed_keys.append(key)
            elif result.get(key) != val:
                is_pass = False
                failed_keys.append(key)
        
        status = "PASS" if is_pass else "FAIL"
        results.append({
            "query": query,
            "status": status,
            "expected": expected,
            "got": result,
            "failed_keys": failed_keys
        })
        
        if not is_pass:
            print(f"  FAIL")
            failed += 1
            
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)

            
    # print(f"\n{len(test_cases) - failed}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    run_tests()
