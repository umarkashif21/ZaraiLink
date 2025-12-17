import os
import django
import sys
import json
from datetime import date


sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_data.models import Transaction, CompanyEmbedding
from trade_ledger.services import company, gnn, products, partners

def run_verification():
    print("=== STARTING VERIFICATION ===")
    
    
    tx_count = Transaction.objects.count()
    print(f"Total Transactions: {tx_count}")
    if tx_count == 0:
        print("[FAIL] No transactions found!")
        return

    
    top_buyer = Transaction.objects.values('buyer').annotate(
        vol=django.db.models.Sum('qty_mt')
    ).order_by('-vol').first()
    
    if not top_buyer:
        print("[FAIL] Could not find any buyer.")
        return
        
    company_name = top_buyer['buyer']
    print(f"Testing with Company: {company_name}")

    
    print("\n--- Overview Page Services ---")
    
    
    try:
        inf = gnn.get_network_influence(company_name)
        print(f"Influence Score: {inf.get('combined_score')} (PR: {inf.get('pagerank')}, Deg: {inf.get('degree')})")
    except Exception as e:
        print(f"[FAIL] Influence Score: {e}")

    
    try:
        metrics = company.get_company_overview_metrics(company_name, direction='import')
        print(f"MoM Growth: {metrics.get('mom_growth_pct')}%")
        print(f"Top Products (Share %):")
        for p in metrics.get('top_products', [])[:2]:
            print(f"  - {p['name']}: {p.get('share_pct', 'N/A')}%")
    except Exception as e:
        print(f"[FAIL] Company Metrics: {e}")

    
    try:
        partners_list = partners.get_top_partners(company_name, direction='import', limit=3)
        print(f"Top Partners: {len(partners_list)} found")
    except Exception as e:
        print(f"[FAIL] Partners: {e}")


    
    print("\n--- Product Page Services ---")
    
    
    try:
        perf = products.get_company_product_performance(company_name, direction='import')
        print(f"Product Performance (Top 1):")
        if perf:
            p = perf[0]
            print(f"  - {p['product_name']}: Vol={p['total_volume']}, MoM={p.get('mom_growth_pct')}%")
        else:
            print("  - No products found")
    except Exception as e:
        print(f"[FAIL] Product Performance: {e}")

    
    print("\n--- Portfolio Similarity ---")
    try:
        
        
        sims = products.get_portfolio_similarity(company_name)
        print(f"Similar Portfolios: {[s['company'] for s in sims]}")
    except Exception as e:
        print(f"[FAIL] Portfolio Similarity: {e}")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    run_verification()
