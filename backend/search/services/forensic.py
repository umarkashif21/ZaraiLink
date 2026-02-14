"""
Forensic test for parser attributes.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

def inspect_query(query):
    print(f"\nScanning: '{query}'")
    url = f"{BASE_URL}?q={query}&scope=WORLDWIDE"
    try:
        resp = requests.get(url)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        print(f"  Intent: {parsed.get('intent')}")
        print(f"  Family: {parsed.get('family')}")
        print(f"  Product: '{parsed.get('product')}'")
        print(f"  Result Count: {len(results)}")
        
        # Check 'Top N' extraction
        import re
        pattern = r'\b(?:top|best|first|suggest)\s+(\d+)\b'
        match = re.search(pattern, query.lower())
        print(f"  Top N Regex Match: {match.group(1) if match else 'None'}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import time
    print("TEST 1: Top 3 dextrose suppliers")
    inspect_query("Top 3 dextrose suppliers")
    time.sleep(2)
    
    print("\nTEST 2: Hybrid")
    inspect_query("Top 3 exporters in China for 40MT under 650 for dextrose")
    time.sleep(2)
    
    print("\nTEST 3: Cheaper than")
    inspect_query("Find dextrose cheaper than 1000")
