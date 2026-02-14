"""
Reproduction script for Seller Query failures (Scope=WORLDWIDE).
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/search/"
SCOPE = "WORLDWIDE"  # User says this means Pakistani sellers looking for Foreign Buyers

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
    products = ["chocolate", "sugar", "dextrose"]
    
    for p in products:
        print(f"\n================ INSPECTING: {p} ================")
        # Query for exporters (Worldwide Sellers looking for buyers)
        # This returns list of Buyers + Destination Countries
        query = f"{p} exporters"
        print(f"Query: '{query}'")
        url = f"{BASE_URL}?q={query}&scope={SCOPE}"
        try:
            resp = requests.get(url)
            results = resp.json().get('results', [])
            print(f"Total Results: {len(results)}")
            
            if not results:
                continue
                
            # Collect countries
            countries = sorted(list(set(r.get('country') for r in results if r.get('country'))))
            print(f"Destination Countries ({len(countries)}): {countries}")
            
            if "Italy" in countries:
                print("✅ ITALY FOUND!")
            else:
                print("❌ ITALY NOT FOUND")
                
            if "Afghanistan" in countries:
                print("✅ AFGHANISTAN FOUND!")
            else:
                print("❌ AFGHANISTAN NOT FOUND")

            # Collect Stats
            max_vol = max((r.get('max_shipment_vol') or 0) for r in results)
            avg_price = sum((r.get('avg_price') or 0) for r in results) / len(results)
            max_price = max((r.get('avg_price') or 0) for r in results)
            
            print(f"Max Shipment Vol (Any Buyer): {max_vol} MT")
            print(f"Max Price Seen: ${max_price}")
            print(f"Avg Price: ${avg_price:.2f}")

        except Exception as e:
            print(f"Error: {e}")
