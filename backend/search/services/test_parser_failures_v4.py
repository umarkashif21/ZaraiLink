"""
Check Parser Output for Remaining Failures.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "WORLDWIDE"

def check(query):
    print(f"\nQUERY: '{query}'")
    params = {'q': query, 'scope': SCOPE}
    try:
        resp = requests.get(BASE_URL, params=params)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        print(f"Parsed: {json.dumps(parsed, indent=2)}")
        print(f"Total Results: {len(data.get('results', []))}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check("I have 100MT of chocolate")
    check("Looking to sell 200MT of chocolate")
    check("buyers paying more than refined sugar above $500")
    check("who buys refined sugar above $500") # Baseline (Works)
    check("Buyers in Afghanistan who pay above $500 for refined sugar")
    check("Find refined sugar buyers in Afghanistan paying above $510") # Baseline (Works)
