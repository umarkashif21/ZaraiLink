"""
Debug specific hybrid query failure.
Query: "Find dextrose suppliers under $800 and list top 5"
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

def debug(query):
    print(f"\nScanning: '{query}'")
    url = f"{BASE_URL}?q={query}&scope=WORLDWIDE"
    try:
        resp = requests.get(url)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        print(f"  Multi-Intent: {parsed.get('multi_intent')}")
        if parsed.get('multi_intent'):
             for i, sub in enumerate(parsed.get('sub_intents', [])):
                 print(f"    Sub {i}: {sub}")
                 
        print(f"  Result Count: {len(results)}")
        if len(results) == 0:
            print("  ❌ ZERO RESULTS")
            # Check components
            print("  Checking components...")
            # 1. Price only
            q1 = "dextrose under 800"
            r1 = requests.get(f"{BASE_URL}?q={q1}&scope=WORLDWIDE").json()
            print(f"    '{q1}': {len(r1.get('results', []))} results")
            
            # 2. Product only
            q2 = "dextrose"
            r2 = requests.get(f"{BASE_URL}?q={q2}&scope=WORLDWIDE").json()
            print(f"    '{q2}': {len(r2.get('results', []))} results")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug("Find dextrose suppliers under $800 and list top 5")
