"""
Diagnose Final Seller Failures.
Compare Failing vs Working queries to spot Parser differences.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "WORLDWIDE"

def compare(name, failing_query, working_query=None):
    print(f"\n=== {name} ===")
    
    # 1. Failing
    print(f"FAILING: '{failing_query}'")
    params = {'q': failing_query, 'scope': SCOPE}
    try:
        data = requests.get(BASE_URL, params=params).json()
        parsed = data.get('parsed_query', {})
        results = len(data.get('results', []))
        print(f"  Results: {results}")
        print(f"  Parsed: {json.dumps(parsed, indent=2)}")
    except Exception as e: print(e)

    if working_query:
        # 2. Working
        print(f"WORKING: '{working_query}'")
        params = {'q': working_query, 'scope': SCOPE}
        try:
            data = requests.get(BASE_URL, params=params).json()
            parsed = data.get('parsed_query', {})
            results = len(data.get('results', []))
            print(f"  Results: {results}")
            print(f"  Parsed: {json.dumps(parsed, indent=2)}")
        except Exception as e: print(e)

if __name__ == "__main__":
    # 1. Price Query Discrepancy
    compare("Price Discrepancy", 
            "buyers paying more than refined sugar above $500", 
            "who buys refined sugar above $500")

    # 2. Volume Failure (Chocolate vs Sugar)
    # User says Chocolate fails. I suspect data limit. Testing Sugar (known high vol matches) to confirm Logic.
    compare("Volume Logic Check", 
            "Looking to sell 100MT of chocolate",
            "Looking to sell 100MT of sugar") 

    # 3. Hybrid Parsing
    compare("Hybrid Parsing", 
            "Buyers in Afghanistan who pay above $500",
            "Find refined sugar buyers in Afghanistan paying above $510")
