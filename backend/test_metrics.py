import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
import django
django.setup()

from trade_ledger.services.explorer import get_explorer_companies
from trade_ledger.services.company import get_company_overview_metrics
from trade_ledger.services.gnn import get_similar_companies, get_network_influence

print("=" * 50)
print("TESTING STATIC METRICS")
print("=" * 50)


print("\n1. Explorer Service - Top 5 Companies:")
results = get_explorer_companies(direction='import', limit=5)
for r in results:
    print(f"   - {r['company']}: {float(r['total_volume']):.2f} MT, Partners: {r['active_partners']}")


if results:
    company_name = results[0]['company']
    print(f"\n2. Company Overview for '{company_name}':")
    metrics = get_company_overview_metrics(company_name, direction='import')
    print(f"   - Revenue: ${float(metrics['est_revenue_usd']):,.2f}")
    print(f"   - Total Volume: {float(metrics['total_volume_mt']):,.2f} MT")
    print(f"   - Active Partners: {metrics['active_partners']}")
    print(f"   - MoM Growth: {metrics['mom_growth_pct']}%")

    
    print(f"\n3. Similar Companies (GNN):")
    similar = get_similar_companies(company_name, top_k=3)
    if similar:
        for s in similar:
            print(f"   - {s['company_name']}: Similarity {s['similarity']:.3f}, Tag: {s['segment_tag']}")
    else:
        print("   No similar companies found (company may not have embedding)")
    
    
    print(f"\n4. Network Influence (GNN):")
    influence = get_network_influence(company_name)
    print(f"   - PageRank: {influence['pagerank']:.6f}")
    print(f"   - Degree: {influence['degree']}")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 50)
