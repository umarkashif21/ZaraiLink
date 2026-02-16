import os
import django
import sys
import json

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()

from search.services.nlp import QueryMatcher
from search.services.aggregation import SupplierAggregator

def run_verify():
    out = {}
    
    # NLP Step
    matcher = QueryMatcher()
    matches = matcher.match("buy dextrose anhydrous")
    
    out['nlp_matches'] = matches
    
    matched_variant_ids = []
    top_subcat_ids = []
    
    if matches:
        # Simulate View Logic
        top_match = matches[0]
        threshold = top_match['score'] - 0.05
        top_subcats = [m for m in matches if m['score'] >= threshold]
        
        top_subcat_ids = [m['id'] for m in top_subcats]
        out['top_subcat_ids'] = top_subcat_ids
        
        target_ids = set(top_subcat_ids)
        for m in matches:
             if m['id'] in target_ids and m.get('matched_variants'):
                 matched_variant_ids.extend(m['matched_variants'])
                 
        matched_variant_ids = list(set(matched_variant_ids))
        out['auto_variants'] = matched_variant_ids
        
        # Aggregation Step
        agg = SupplierAggregator()
        results = agg.get_suppliers_for_subcategories(
            top_subcat_ids,
            product_item_filter=matched_variant_ids
        )
        out['results_count'] = len(results)
        out['results_top_5'] = results[:5]
        
    else:
        out['error'] = "No NLP matches"

    with open('verify_result.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)

if __name__ == "__main__":
    run_verify()
