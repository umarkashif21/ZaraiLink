"""
Verification for hybrid queries.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/search/"

def test(query):
    print(f"\nScanning: '{query}'")
    url = f"{BASE_URL}?q={query}&scope=WORLDWIDE"
    try:
        resp = requests.get(url)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        print(f"  Multi-Intent: {parsed.get('multi_intent')}")
        if parsed.get('multi_intent'):
             print(f"  Sub-intents: {len(parsed.get('sub_intents', []))}")
             
        # Check if merging worked (filters applied?)
        print(f"  MERGED PARAMS USED BY BACKEND (INFERRED):")
        # We can infer from results or debug log, but here we check results count
        print(f"  Result Count: {len(results)}")
        
        if len(results) > 0:
            r = results[0]
            print(f"  Top Result: {r.get('counterparty_name')} ({r.get('country')})")
            print(f"  Price: ${r.get('avg_price_usd_per_mt')}")
            print(f"  Volume: {r.get('total_volume_mt')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("TEST 1: Split Hybrid")
    test("Find dextrose suppliers in China under 700 and suggest top 3")
    time.sleep(2)
    
    print("\nTEST 2: Complex Single")
    test("Top 3 fructose suppliers in China for 40MT under 650")
    time.sleep(2)
    
    print("\nTEST 3: Another Hybrid")
    test("I want 50MT of fructose from Brazil")
