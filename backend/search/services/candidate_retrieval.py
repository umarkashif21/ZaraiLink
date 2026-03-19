from .vector_store import FaissVectorStore
from .aggregation import SupplierAggregator
from trade_data.models import ProductSubCategory
import datetime

class CandidateRetriever:
    def __init__(self):
        self.vector_store = FaissVectorStore()
        
    def retrieve_candidates(self, parsed_query, scope=None):
        """
        Orchestrates candidate retrieval from modern parsed query dict.
        """
        # 1. Scope Resolution
        scope = scope or parsed_query.get('scope', 'WORLDWIDE')
        
        # Handle Multi-Intent (Focus on first for now)
        if parsed_query.get('multi_intent') and parsed_query.get('sub_intents'):
            active_params = parsed_query['sub_intents'][0]
        else:
            active_params = parsed_query
            
        # Extract Parameters
        product_term = active_params.get('product')
        expanded_terms = active_params.get('expanded_terms', [])
        intent = active_params.get('intent', 'BUY')
        country_filter = active_params.get('country_filter', [])
        volume_req = active_params.get('volume_mt')
        
        # Price Filter construction
        price_filter = {}
        if active_params.get('price_ceiling'):
            price_filter['ceiling'] = active_params['price_ceiling']
        if active_params.get('price_floor'):
            price_filter['floor'] = active_params['price_floor']
            
        time_filter = self._parse_time_range(active_params.get('time_range'))
            
        # 2. Product Matching (Hybrid Search Pipeline)
        matched_category_ids = self._hybrid_search(product_term, expanded_terms)
        
        if not matched_category_ids:
            return [] 
            
        # 3. Aggregation (Fetch Suppliers from Transactions)
        aggregator = SupplierAggregator()
        raw_results = aggregator.get_suppliers_for_subcategories(
            matched_category_ids,
            intent=intent,
            scope=scope,
            country_filter=country_filter,
            price_filter=price_filter,
            volume_filter=volume_req, 
            time_filter=time_filter
        )
        
        # 4. Final Formatting
        return self._format_candidates(raw_results, active_params, volume_req)

    def _hybrid_search(self, product_term, expanded_terms):
        """Combines Dense (FAISS) and Sparse (Lexical) retrieval for high recall & precision."""
        if not product_term:
            return []

        search_pool = set()
        
        # A. Sparse / Lexical Search (High Precision for exact matches)
        lexical_hits = ProductSubCategory.objects.filter(name__icontains=product_term)
        for hit in lexical_hits:
            search_pool.add(hit.id)
            
        # B. Dense / Semantic Search (High Recall for synonyms/concepts) via FAISS
        try:
            semantic_hits = self.vector_store.search(product_term, top_k=10, cache_expand=expanded_terms)
            for hit in semantic_hits:
                search_pool.add(hit['id'])
        except Exception as e:
            # Fallback gracefully if FAISS isn't initialized yet
            pass

        return list(search_pool)

    def _format_candidates(self, raw_results, active_params, volume_req):
        formatted = []
        for r in raw_results:
            # Volume Fit Logic
            volume_fit = "N/A"
            if volume_req:
                max_vol = r.get('max_shipment_vol', 0)
                total_vol = r.get('total_volume', 0)
                
                if max_vol >= volume_req * 1.2:
                    volume_fit = "Strong"
                elif max_vol >= volume_req:
                    volume_fit = "Good"
                elif total_vol >= volume_req:
                    volume_fit = "Partial"
                else:
                    volume_fit = "Low"

            # Check if this counterparty was explicitly mentioned in NER
            ner_boost = 0
            if active_params.get('counterparty_name') and active_params['counterparty_name'].lower() in r['name'].lower():
                ner_boost = 1 # We can use this to bubble them up later
                
            formatted.append({
                "counterparty_name": r['name'],
                "total_volume_mt": r['total_volume'],
                "avg_price_usd_per_mt": r['avg_price'],
                "num_shipments": r['shipment_count'],
                "last_trade_date": r['last_shipment_date'].isoformat() if r['last_shipment_date'] else None,
                "product_subcategories": [active_params.get('product')], 
                "volume_fit": volume_fit,
                "ner_exact_match": bool(ner_boost)
            })
        return formatted

    def _parse_time_range(self, time_range_str):
        if not time_range_str:
            return None
            
        today = datetime.date.today()
        start_date = None
        end_date = None
        tr = time_range_str.lower().strip()
        
        if "q1" in tr and "2025" in tr:
            start_date = datetime.date(2025, 1, 1)
            end_date = datetime.date(2025, 3, 31)
        elif "2025" in tr:
            start_date = datetime.date(2025, 1, 1)
            end_date = datetime.date(2025, 12, 31)
        elif "2024" in tr:
            start_date = datetime.date(2024, 1, 1)
            end_date = datetime.date(2024, 12, 31)
        elif "last 6 months" in tr:
            end_date = today
            start_date = today - datetime.timedelta(days=180)
            
        if start_date or end_date:
            return {"start_date": start_date, "end_date": end_date}
        return None
