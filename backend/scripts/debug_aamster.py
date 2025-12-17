import os
import django
import sys


sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.services.company import get_company_overview_metrics
from trade_ledger.services.products import get_company_product_performance

def debug_aamster():
    company = "Aamster Laboratories (Branch)"
    print(f"Debugging: {company}")
    
    
    metrics = get_company_overview_metrics(company, direction='import')
    print(f"Overview (Import) Vol: {metrics['total_volume_mt']}")
    print(f"Overview (Import) Products: {len(metrics['top_products'])}")
    for p in metrics['top_products']:
        print(f" - {p['name']} ({p.get('share_pct')}%)")

    
    perf = get_company_product_performance(company, direction='import')
    print(f"Products Tab (Import) Count: {len(perf)}")
    
    
    metrics_ex = get_company_overview_metrics(company, direction='export')
    print(f"Overview (Export) Vol: {metrics_ex['total_volume_mt']}")
    print(f"Overview (Export) Products: {len(metrics_ex['top_products'])}")

if __name__ == "__main__":
    debug_aamster()
