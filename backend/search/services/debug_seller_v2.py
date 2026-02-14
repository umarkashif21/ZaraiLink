"""
Debug specific Seller query failures.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "WORLDWIDE"

def test(query):
    print(f"\nQUERY: '{query}'")
    url = f"{BASE_URL}?q={query}&scope={SCOPE}"
    try:
        resp = requests.get(url)
        data = resp.json()
        results = data.get('results', [])
        parsed = data.get('parsed_query', {})
        
        print(f"  Parsed: {json.dumps(parsed, indent=2)}")
        print(f"  Total Results: {len(results)}")
        
        if len(results) > 0:
            countries = list(set([r.get('country') for r in results]))
            print(f"  Countries found: {countries[:5]}")
            # Check volumes
            max_vol = max([r.get('max_shipment_vol') or 0 for r in results])
            print(f"  Max Shipment Vol found: {max_vol}")
            # Check prices
            max_price = max([r.get('avg_price') or 0 for r in results])
            print(f"  Max Price found: {max_price}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Baseline
    test("who buys refined sugar")
    
    # Country Failure
    test("refined sugar buyers in Afghanistan")
    
    # Volume Failure
    test("I have 100MT of chocolate") # Check if parsed correctly
    test("Looking to sell 100MT of chocolate")
    
    # Price Failure
    test("can i sell refined sugar above $500")
