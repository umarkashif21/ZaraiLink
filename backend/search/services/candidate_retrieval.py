from .nlp import QueryMatcher
from .aggregation import SupplierAggregator

import datetime

class CandidateRetriever:
    def retrieve_candidates(self, parsed_query, scope=None):
        """
        Orchestrates candidate retrieval from parsed query.
        """
        # 1. Scope Resolution
        scope = scope or 'WORLDWIDE'
        
        # 2. Handle Multi-Intent (Focus on first for now)
        if parsed_query.get('multi_intent') and parsed_query.get('sub_intents'):
            # Optimization: could return dict of results per intent, but for now take first
            active_params = parsed_query['sub_intents'][0]
        else:
            active_params = parsed_query
            
        # 3. Extract Parameters
        product_term = active_params.get('product')
        intent = active_params.get('intent', 'BUY')
        country_filter = active_params.get('country_filter', [])
        volume_req = active_params.get('volume_mt')
        time_range_str = active_params.get('time_range')
        
        # Price Filter construction
        price_filter = {}
        if active_params.get('price_ceiling'):
            price_filter['ceiling'] = active_params['price_ceiling']
        if active_params.get('price_floor'):
            price_filter['floor'] = active_params['price_floor']
            
        # Time Filter Parsing
        time_filter = self._parse_time_range(time_range_str)
            
        # 4. Product Mapping (NLP)
        matcher = QueryMatcher()
        matched_category_ids = []
        if product_term:
            matches = matcher.match(product_term)
            # Thresholding logic? Aggregator usually handles 'all matches' or 'top match'
            # Let's pass all matches for now to be safe, or top N
            matched_category_ids = [m['id'] for m in matches]
        
        if not matched_category_ids:
            return [] # No product found, no candidates
            
        # 5. Aggregation
        aggregator = SupplierAggregator()
        raw_results = aggregator.get_suppliers_for_subcategories(
            matched_category_ids,
            intent=intent,
            scope=scope,
            country_filter=country_filter,
            price_filter=price_filter,
            volume_filter=volume_req, # Pass requested volume filter (Aggregator uses this as min capacity)
            time_filter=time_filter
        )
        
        # 6. Formatting
        formatted_results = []
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

            formatted_results.append({
                "counterparty_name": r['name'],
                "total_volume_mt": r['total_volume'],
                "avg_price_usd_per_mt": r['avg_price'],
                "num_shipments": r['shipment_count'],
                "last_trade_date": r['last_shipment_date'].isoformat() if r['last_shipment_date'] else None,
                "product_subcategories": [active_params.get('product')], # Contextual, or fetch names from IDs
                "volume_fit": volume_fit
            })
            
        return formatted_results

    def _parse_time_range(self, time_range_str):
        """
        Parses strings like "Q1 2025", "2024", "Last 6 Months".
        Returns dict {start_date, end_date} or None.
        """
        if not time_range_str:
            return None
            
        today = datetime.date.today()
        start_date = None
        end_date = None
        
        tr = time_range_str.lower().strip()
        
        # Simple heuristics
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
