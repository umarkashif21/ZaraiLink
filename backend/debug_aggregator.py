
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from search.services.aggregation import SupplierAggregator

def test_agg(subcat_id, intent='BUY', scope='WORLDWIDE'):
    with open('debug_agg_output.txt', 'a') as f:
        f.write(f"\nTesting: Subcat {subcat_id} | Intent {intent} | Scope {scope}\n")
        agg = SupplierAggregator()
        results = agg.get_suppliers_for_subcategories([subcat_id], intent=intent, scope=scope)
        f.write(f"Results count: {len(results)}\n")
        if len(results) > 0:
            f.write(f"Top result: {results[0]['name']} ({results[0]['total_volume']} MT)\n")

if __name__ == "__main__":
    if os.path.exists('debug_agg_output.txt'):
        os.remove('debug_agg_output.txt')
        
    # Dextrose Anhydrous (717)
    test_agg(717, 'BUY', 'WORLDWIDE')
    test_agg(717, 'BUY', 'PAKISTAN')
    
    # Fructose (726)
    test_agg(726, 'BUY', 'WORLDWIDE')
    test_agg(726, 'BUY', 'PAKISTAN')
