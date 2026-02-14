"""
Test script to diagnose query type issues for buyer queries with worldwide scope.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

# Test queries for each type
test_queries = {
    "volume": [
        "I need 50MT of dextrose",
        "Buy 2000kg sugar",
        "Looking for 100MT rice"
    ],
    "price": [
        "Buy dextrose under 700",
        "Sugar below 500",
        "Rice cheaper than 900"
    ],
    "recommendation": [
        "Top 3 dextrose suppliers",
        "Best suppliers for 50MT sugar",
        "Suggest good glucose syrup suppliers"
    ],
    "hybrid": [
        "Find suppliers in China under 700 and suggest top 3",
        "I want 50MT of sugar from Brazil",
        "Top 3 exporters in China for 40MT under 650 for dextrose"
    ]
}

def test_query(query, scope="WORLDWIDE"):
    """Test a single query and return diagnostics."""
    url = f"{BASE_URL}?q={query}&scope={scope}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        parsed = data.get('parsed_query', {})
        results = data.get('results', [])
        
        return {
            "query": query,
            "status": "SUCCESS" if response.status_code == 200 else "ERROR",
            "intent": parsed.get('intent'),
            "family": parsed.get('family'),
            "volume_mt": parsed.get('volume_mt'),
            "price_ceiling": parsed.get('price_ceiling'),
            "price_floor": parsed.get('price_floor'),
            "country_filter": parsed.get('country_filter'),
            "multi_intent": parsed.get('multi_intent'),
            "result_count": len(results),
            "top_3_results": [
                {
                    "name": r.get('counterparty_name'),
                    "avg_price": r.get('avg_price_usd_per_mt'),
                    "total_volume": r.get('total_volume_mt')
                }
                for r in results[:3]
            ]
        }
    except Exception as e:
        return {
            "query": query,
            "status": "EXCEPTION",
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("BUYER QUERY TYPE DIAGNOSTICS - WORLDWIDE SCOPE")
    print("=" * 80)
    
    for query_type, queries in test_queries.items():
        print(f"\n{'='*80}")
        print(f"Testing: {query_type.upper()}")
        print(f"{'='*80}")
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            print("-" * 80)
            
            result = test_query(query)
            
            if result['status'] == 'SUCCESS':
                print(f"✓ Status: {result['status']}")
                print(f"  Intent: {result['intent']}")
                print(f"  Family: {result['family']}")
                print(f"  Volume: {result['volume_mt']} MT" if result['volume_mt'] else "  Volume: None")
                print(f"  Price Ceiling: ${result['price_ceiling']}" if result['price_ceiling'] else "  Price Ceiling: None")
                print(f"  Price Floor: ${result['price_floor']}" if result['price_floor'] else "  Price Floor: None")
                print(f"  Country Filter: {result['country_filter']}")
                print(f"  Multi-Intent: {result['multi_intent']}")
                print(f"  Result Count: {result['result_count']}")
                
                if result['top_3_results']:
                    print(f"\n  Top 3 Results:")
                    for i, r in enumerate(result['top_3_results'], 1):
                        name = r['name'] or 'N/A'
                        price = r['avg_price'] if r['avg_price'] is not None else 0
                        volume = r['total_volume'] if r['total_volume'] is not None else 0
                        print(f"    {i}. {name} - ${price:.2f}/MT - {volume:.2f} MT")
                        
                # Diagnostics
                print(f"\n  🔍 DIAGNOSTICS:")
                
                if query_type == "volume" and result['volume_mt']:
                    print(f"    ✓ Volume extracted: {result['volume_mt']} MT")
                    if result['result_count'] > 0:
                        print(f"    ⚠️ Check if results filtered by volume capacity")
                    else:
                        print(f"    ❌ No results - volume filter too strict?")
                        
                if query_type == "price" and (result['price_ceiling'] or result['price_floor']):
                    print(f"    ✓ Price constraint extracted")
                    if result['result_count'] > 0:
                        print(f"    ⚠️ Check if results respect price constraint")
                    else:
                        print(f"    ❌ No results - price filter too strict?")
                        
                if query_type == "recommendation" and result['family'] == 6:
                    print(f"    ✓ Family 6 (Recommendation) detected")
                    if result['result_count'] > 10:
                        print(f"    ❌ BUG: Returning {result['result_count']} results instead of top N")
                    else:
                        print(f"    ✓ Result count looks reasonable: {result['result_count']}")
                        
                if query_type == "hybrid" and result['multi_intent']:
                    print(f"    ✓ Multi-intent detected")
                    print(f"    ⚠️ Check if all intents processed or just first")
                    
            else:
                print(f"✗ Status: {result['status']}")
                print(f"  Error: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    main()
