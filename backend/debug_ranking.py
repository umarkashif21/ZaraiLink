
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')
django.setup()
from search.services.aggregation import SupplierAggregator
from search.services.ranking_ltr import RankingEnsemble

def test_rank(subcat_id):
    with open('debug_ranking_output.txt', 'a') as f:
        f.write(f"\n--- Testing Ranking for Subcat {subcat_id} ---\n")
        
        # 1. Aggregate
        agg = SupplierAggregator()
        candidates = agg.get_suppliers_for_subcategories([subcat_id], intent='BUY', scope='WORLDWIDE')
        f.write(f"Aggregator returned: {len(candidates)} candidates\n")
        
        if not candidates:
            return

        # 2. Rank
        ranker = RankingEnsemble()
        # Mock parsed query
        parsed_query = {'intent': 'BUY', 'scope': 'WORLDWIDE', 'country_filter': []}
        
        try:
            ranked = ranker.rank_candidates(candidates, parsed_query)
            f.write(f"Ranker returned: {len(ranked)} candidates\n")
            if ranked:
                 f.write(f"Top 1: {ranked[0]['name']} (Score: {ranked[0].get('ranking_score')})\n")
        except Exception as e:
            f.write(f"Ranker CRASHED: {e}\n")

if __name__ == "__main__":
    if os.path.exists('debug_ranking_output.txt'):
         os.remove('debug_ranking_output.txt')
    test_rank(717) # Dextrose Anhydrous
    test_rank(726) # Fructose
