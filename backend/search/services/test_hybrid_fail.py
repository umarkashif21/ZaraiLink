"""
Reproduction script for hybrid/multi-intent failures.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/search/"

def test(query):
    print(f"\nTesting: '{query}'")
    url = f"{BASE_URL}?q={query}&scope=WORLDWIDE"
    try:
        resp = requests.get(url)
        data = resp.json()
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        print(f"  Intent: {parsed.get('intent')}")
        print(f"  Family: {parsed.get('family')}")
        print(f"  Multi-Intent: {parsed.get('multi_intent')}")
        if parsed.get('multi_intent'):
            print(f"  Sub-intents: {len(parsed.get('sub_intents', []))}")
            for i, sub in enumerate(parsed.get('sub_intents', [])):
                print(f"    {i}: Family={sub.get('family')}, Intent={sub.get('intent')}")
                
        print(f"  Result Count: {len(results)}")
        if len(results) > 0:
            print(f"  Top Result: {results[0].get('counterparty_name')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Query 1: Multi-intent split issue
    test("Find suppliers in China under 700 and suggest top 3")
    time.sleep(1)
    
    # Query 2: Intent detection issue ("exporters" -> SELL?)
    test("Top 3 exporters in China for 40MT under 650 for dextrose")
