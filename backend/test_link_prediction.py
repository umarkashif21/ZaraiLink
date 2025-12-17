import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from trade_ledger.services.link_prediction import (
    predict_sellers_node2vec,
    predict_sellers_common_neighbors,
    predict_sellers_by_product,
    predict_sellers_jaccard,
    predict_sellers_preferential_attachment,
    predict_sellers_combined
)

buyer = "Nestle Pakistan Ltd"

print("=" * 60)
print(f"LINK PREDICTION TEST FOR: {buyer}")
print("=" * 60)


print("\n1. NODE2VEC SIMILARITY:")
result = predict_sellers_node2vec(buyer, top_k=5)
if result.get('error'):
    print(f"   Error: {result['error']}")
else:
    for r in result['results'][:3]:
        print(f"   - {r['seller'][:40]}... Score: {r['score']:.4f}")

print("\n2. COMMON NEIGHBORS:")
result = predict_sellers_common_neighbors(buyer, top_k=5)
if result.get('error'):
    print(f"   Error: {result['error']}")
else:
    for r in result['results'][:3]:
        print(f"   - {r['seller'][:40]}... Common: {r['common_buyer_count']}")

print("\n3. PRODUCT CO-TRADE:")
result = predict_sellers_by_product(buyer, top_k=5)
if result.get('error'):
    print(f"   Error: {result['error']}")
else:
    for r in result['results'][:3]:
        print(f"   - {r['seller'][:40]}... Products: {r['matching_products']}")

print("\n4. JACCARD COEFFICIENT:")
result = predict_sellers_jaccard(buyer, top_k=5)
if result.get('error'):
    print(f"   Error: {result['error']}")
else:
    for r in result['results'][:3]:
        print(f"   - {r['seller'][:40]}... Score: {r['score']:.4f}")

print("\n5. PREFERENTIAL ATTACHMENT:")
result = predict_sellers_preferential_attachment(buyer, top_k=5)
if result.get('error'):
    print(f"   Error: {result['error']}")
else:
    for r in result['results'][:3]:
        print(f"   - {r['seller'][:40]}... Connections: {r['seller_connections']}")

print("\n6. COMBINED (ALL METHODS):")
result = predict_sellers_combined(buyer, top_k=5)
for r in result['results'][:5]:
    print(f"   - {r['seller'][:40]}...")
    print(f"     Total Score: {r['total_score']:.4f}")
    print(f"     Methods: {list(r['scores'].keys())}")

print("\n" + "=" * 60)
print("LINK PREDICTION TESTS COMPLETE!")
print("=" * 60)
