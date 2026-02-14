"""
Simple manual test for the 4 query types.
Run this to test individual queries and inspect output.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

def test_single_query(query, scope="WORLDWIDE"):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"Testing: {query}")
    print(f"Scope: {scope}")
    print(f"{'='*80}\n")
    
    url = f"{BASE_URL}?q={query}&scope={scope}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Pretty print the parsed query
        parsed = data.get('parsed_query', {})
        print("PARSED QUERY:")
        print(f"  Intent: {parsed.get('intent')}")
        print(f"  Family: {parsed.get('family')}")
        print(f"  Product: {parsed.get('product')}")
        print(f"  Volume: {parsed.get('volume_mt')} MT" if parsed.get('volume_mt') else "  Volume: None")
        print(f"  Price Ceiling: ${parsed.get('price_ceiling')}" if parsed.get('price_ceiling') else "  Price Ceiling: None")
        print(f"  Price Floor: ${parsed.get('price_floor')}" if parsed.get('price_floor') else "  Price Floor: None")
        print(f"  Country Filter: {parsed.get('country_filter')}")
        print(f"  Time Range: {parsed.get('time_range')}")
        print(f"  Multi-Intent: {parsed.get('multi_intent')}")
        
        # Results
        results = data.get('results', [])
        print(f"\nRESULTS: {len(results)} suppliers found")
        
        if results:
            print("\nTop 5:")
            for i, r in enumerate(results[:5], 1):
                name = r.get('counterparty_name', 'N/A')
                price = r.get('avg_price_usd_per_mt')
                volume = r.get('total_volume_mt')
                country = r.get('country', 'N/A')
                print(f"  {i}. {name} ({country})")
                if price:
                    print(f"     Price: ${price:.2f}/MT")
                if volume:
                    print(f"     Volume: {volume:.2f} MT")
        
        return data
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    # Test each type
    print("\n" + "="*80)
    print("MANUAL QUERY TYPE TESTS - WORLDWIDE SCOPE")
    print("="*80)
    
    # 1. Volume-Constrained
    test_single_query("I need 50MT of dextrose")
    
    # 2. Price-Constrained
    test_single_query("Buy dextrose under 700")
    
    # 3. Recommendation
    test_single_query("Top 3 dextrose suppliers")
    
    # 4. Hybrid
    test_single_query("Top 3 exporters in China for 40MT under 650 for dextrose")
