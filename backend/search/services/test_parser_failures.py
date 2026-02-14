"""
Check Parser Output for Failing Queries.
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
    check("refined sugar buyers in Afghanistan")
    check("I have 100MT of chocolate")
    check("can i sell refined sugar above $500")
