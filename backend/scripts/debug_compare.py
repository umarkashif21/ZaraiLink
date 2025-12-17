import os
import django
import sys
import json


sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from trade_ledger.services.compare import get_company_comparison_metrics
from trade_data.models import Transaction, CompanyEmbedding

def debug_compare():
    companies = ["Aamster Laboratories (Branch)", "Trading Corporation Of Pakistan Pvt Ltd"]
    print(f"Comparing: {companies}")
    
    try:
        metrics = get_company_comparison_metrics(companies, direction='import')
        print("Service metrics computed successfully:")
        print(json.dumps(metrics, indent=2,  default=str))
    except Exception as e:
        print(f"[FAIL] Service Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing View Logic Mock ---")
    companies_data = []
    for name in companies:
        try:
             
            cm = metrics.get(name, {})
            pagerank = 0.0
            degree = 0
            try:
                emb = CompanyEmbedding.objects.get(company_name=name)
                pagerank = float(emb.pagerank)
                degree = emb.degree
            except CompanyEmbedding.DoesNotExist:
                print(f"  - No embedding for {name}")
                pass
            
            product_count = Transaction.objects.filter(buyer=name).values('product_item').distinct().count()
            
            datum = {
                'name': name,
                'trade_volume': cm.get('total_volume_mt', 0),
                'pagerank': pagerank
            }
            companies_data.append(datum)
            print(f"  - Processed {name}")
        except Exception as e:
             print(f"[FAIL] View Logic Error for {name}: {e}")

    print("Result:", companies_data)

if __name__ == "__main__":
    debug_compare()
