"""
Reproduction script for Seller Query failures (Scope=PAKISTAN).
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "PAKISTAN"  # We are looking for Foreign Buyers for our Pakistani goods

def test(query):
    print(f"\nQuery: '{query}'")
    url = f"{BASE_URL}?q={query}&scope={SCOPE}"
    try:
        resp = requests.get(url)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        print(f"  Intent: {parsed.get('intent')}")
        print(f"  Product: {parsed.get('product')}")
        print(f"  Country Filter: {parsed.get('country_filter')}")
        print(f"  Volume: {parsed.get('volume_mt')}")
        print(f"  Price: {parsed.get('price_floor')} - {parsed.get('price_ceiling')}")
        print(f"  Result Count: {len(results)}")
        
        if len(results) > 0:
            # Check distinct countries if country filter applied
            countries = set(r.get('country') for r in results)
            print(f"  Countries found: {list(countries)[:3]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("--- 1. Simple Discovery (Importers vs Buyers consistency) ---")
    test("who buys chocolate")
    test("chocolate importers")
    
    print("\n--- 2. Country Filtered (Failing?) ---")
    test("chocolate buyers in Italy")
    
    print("\n--- 3. Volume Constrained (Failing?) ---")
    test("I have 100MT of chocolate")
    
    print("\n--- 4. Target Price (Failing?) ---")
    test("buyers paying more than $500 for chocolate")
