"""
Quick test to diagnose the 3 issues
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/search/"

def test_query(query, scope="WORLDWIDE"):
    """Test query and return parsed_query"""
    url = f"{BASE_URL}?q={query}&scope={scope}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}

# Issue A: Volume filtering - how it works
print("="*80)
print("ISSUE A: Volume Filtering Logic")
print("="*80)
result = test_query("I need 50MT of dextrose")
parsed = result.get('parsed_query', {})
print(f"Query: 'I need 50MT of dextrose'")
print(f"  volume_mt extracted: {parsed.get('volume_mt')}")
print(f"  Result count: {len(result.get('results', []))}")
print(f"\nHow it works:")
print(f"  - Aggregator filters: max_shipment_vol >= {parsed.get('volume_mt')} MT")
print(f"  - Only returns suppliers who have shipped >= 50MT in a single shipment")
print(f"  - This proves they CAN handle 50MT orders")

# Issue B: "cheaper than" pattern
print("\n" + "="*80)
print("ISSUE B: 'cheaper than' Pattern")
print("="*80)
result = test_query("Find dextrose cheaper than 1000")
parsed = result.get('parsed_query', {})
print(f"Query: 'Find dextrose cheaper than 1000'")
print(f"  price_ceiling extracted: {parsed.get('price_ceiling')}")
print(f"  price_floor extracted: {parsed.get('price_floor')}")
if not parsed.get('price_ceiling'):
    print("  ❌ ISSUE CONFIRMED: 'cheaper than' not recognized")
else:
    print(f"  ✓ Working: ceiling = ${parsed.get('price_ceiling')}")

# Issue C: "Top 3" recommendation
print("\n" + "="*80)
print("ISSUE C: Recommendation 'Top 3'")
print("="*80)
result = test_query("Top 3 dextrose suppliers")
parsed = result.get('parsed_query', {})
results = result.get('results', [])
print(f"Query: 'Top 3 dextrose suppliers'")
print(f"  Family: {parsed.get('family')}")
print(f"  Result count: {len(results)}")
if len(results) != 3:
    print(f"  ❌ ISSUE CONFIRMED: Returned {len(results)} instead of 3")
else:
    print(f"  ✓ Working: Returns exactly 3")

# Issue C2: Hybrid query
print("\n" + "="*80)
print("ISSUE C2: Hybrid Query")
print("="*80)
result = test_query("Top 3 exporters in China for 40MT under 650 for dextrose")
parsed = result.get('parsed_query', {})
results = result.get('results', [])
print(f"Query: 'Top 3 exporters in China for 40MT under 650 for dextrose'")
print(f"  Family: {parsed.get('family')}")
print(f"  volume_mt: {parsed.get('volume_mt')}")
print(f"  price_ceiling: {parsed.get('price_ceiling')}")
print(f"  country_filter: {parsed.get('country_filter')}")
print(f"  Result count: {len(results)}")
if len(results) != 3:
    print(f"  ❌ ISSUE CONFIRMED: Returned {len(results)} instead of 3")
else:
    print(f"  ✓ Working: Returns exactly 3")
