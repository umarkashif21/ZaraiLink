"""
Inspect Refined Sugar and Afghanistan Data.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "WORLDWIDE"

def inspect(query):
    print(f"\nQUERY: '{query}'")
    # Use params for proper encoding
    params = {'q': query, 'scope': SCOPE}
    try:
        resp = requests.get(BASE_URL, params=params)
        data = resp.json()
        results = data.get('results', [])
        print(f"Total Results: {len(results)}")
        
        if len(results) > 0:
            countries = set()
            for r in results:
                c = r.get('country')
                if c:
                    countries.add(c)
            
            sorted_countries = sorted(list(countries))
            print(f"Countries Found ({len(countries)}):")
            for c in sorted_countries:
                if "afghan" in c.lower() or "italy" in c.lower():
                    print(f"  -> '{c}' (Len: {len(c)})")
            
            # Check Stats
            max_vol = max([r.get('max_shipment_vol') or 0 for r in results])
            max_price = max([r.get('avg_price') or 0 for r in results])
            print(f"Max Vol: {max_vol}")
            print(f"Max Price: {max_price}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # inspect("sugar exporters")
    inspect("who buys refined sugar")
    # inspect("refined sugar exporters")
    # inspect("chocolate exporters")
