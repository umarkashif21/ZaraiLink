
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny # Kept as it was not explicitly removed by the instruction
# from django.conf import settings # Removed as it's not used in the new code

from .services.nlp import QueryMatcher
from .services.aggregation import SupplierAggregator
from .services.ranking import SupplierRanker, ComparableFinder # Added ComparableFinder
# Import models if needed for simple lookups
from trade_data.models import ProductSubCategory # Added

from .services.query_parser import QueryInterpreter # Added

class SearchViewSet(viewsets.ViewSet):
    """
    Unified Search API
    """
    permission_classes = [AllowAny]

    def list(self, request):
        """
        GET /api/search/query/?q=...
        """
        query = request.query_params.get('q', '').strip()
        scope_param = request.query_params.get('scope', None)
        
        # Support POST body for complex queries if needed
        if not query and request.method == 'POST':
            query = request.data.get('q', '')
            scope_param = request.data.get('scope', None)
            
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)

        # 0. Query Interpretation (with explicit scope)
        interpreter = QueryInterpreter()
        parsed_query = interpreter.parse(query, explicit_scope=scope_param)
        
        # Determine search term and merge parameters
        nlp_search_term = query
        active_params = parsed_query
        
        if parsed_query.get('multi_intent') and parsed_query.get('sub_intents'):
            # MERGE Strategy: Combine filters from all sub-intents
            # Start with the first one as base
            merged_params = parsed_query['sub_intents'][0].copy()
            
            for i in range(1, len(parsed_query['sub_intents'])):
                sub = parsed_query['sub_intents'][i]
                
                # 1. Merge Family (Higher family ID usually means more specific intent like Rec/Comparison)
                # Specifically, if one part says "suggest" (Fam 6), the whole query is Fam 6.
                if sub.get('family', 1) > merged_params.get('family', 1):
                    merged_params['family'] = sub['family']
                    
                # 2. Merge Country Filters (Union)
                if sub.get('country_filter'):
                    existing = set(merged_params.get('country_filter', []))
                    existing.update(sub['country_filter'])
                    merged_params['country_filter'] = list(existing)
                    
                # 3. Merge Price (Override if specific provided in later part)
                if sub.get('price_ceiling'):
                    merged_params['price_ceiling'] = sub['price_ceiling']
                if sub.get('price_floor'):
                    merged_params['price_floor'] = sub['price_floor']
                    
                # 4. Merge Volume
                if sub.get('volume_mt'):
                    merged_params['volume_mt'] = sub['volume_mt']
                    
                # 5. Merge Time
                if sub.get('time_range'):
                    merged_params['time_range'] = sub['time_range']
            
            active_params = merged_params
            
            # Use product from first non-empty product sub-intent or default
            for sub in parsed_query['sub_intents']:
                if sub.get('product'):
                    nlp_search_term = sub['product']
                    break
        else:
            nlp_search_term = active_params.get('product') or query 
        
        # Extract Filters from Parser
        intent = active_params.get('intent', 'BUY')
        country_filter = active_params.get('country_filter', [])
        volume_req = active_params.get('volume_mt')
        time_range_str = active_params.get('time_range')
        
        price_filter = {}
        if active_params.get('price_ceiling'):
            price_filter['ceiling'] = active_params['price_ceiling']
        if active_params.get('price_floor'):
            price_filter['floor'] = active_params['price_floor']
            
        # Parse time range
        time_filter = self._parse_time_range(time_range_str) if time_range_str else None
            
        # Extract Manual Filters (Override parser if provided explicitly)
        if request.query_params.get('country'):
             country_filter = [request.query_params.get('country')]
        subcategory_id_filter = request.query_params.get('subcategory_id')

        # Scope + Country conflict detection
        # If scope=PAKISTAN but user specified a non-Pakistan country filter,
        # the filters would conflict (e.g., origin_country='Pakistan' AND origin_country__in=['China']).
        # Return a helpful error instead of silently returning 0 results.
        active_scope = active_params.get('scope', 'WORLDWIDE')
        if active_scope == 'PAKISTAN' and country_filter:
            non_pakistan_countries = [c for c in country_filter if c.lower() != 'pakistan']
            if non_pakistan_countries:
                return Response({
                    "query": query,
                    "parsed_query": parsed_query,
                    "error": "scope_country_conflict",
                    "message": f"You are searching within Pakistan scope but specified {', '.join(non_pakistan_countries)} as a country filter. Please switch your scope to Worldwide to search for international suppliers.",
                    "results": [],
                    "count": 0
                })

        # 1. NLP: Match query to subcategories
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(nlp_search_term)
        
        if not matched_subcategories:
            return Response({
                "query": query,
                "parsed_query": parsed_query,
                "matched_subcategories": [],
                "results": [],
                "message": "No matching products found."
            })

        # 2. Aggregation: Get suppliers/buyers
        if subcategory_id_filter:
            try:
                subcategory_ids = [int(subcategory_id_filter)]
            except ValueError:
                subcategory_ids = [m['id'] for m in matched_subcategories]
        else:
            # Default aggregation logic
            top_match = matched_subcategories[0]
            if top_match['score'] > 0.95:
                threshold = top_match['score'] - 0.05
                subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
            else:
                subcategory_ids = [m['id'] for m in matched_subcategories]
            
        aggregator = SupplierAggregator()
        # Pass parser filters to aggregator
        results = aggregator.get_suppliers_for_subcategories(
            subcategory_ids, 
            intent=intent,
            scope=active_params.get('scope', 'WORLDWIDE'),
            country_filter=country_filter,
            price_filter=price_filter,
            volume_filter=volume_req,
            time_filter=time_filter
        )

        # 3. Ranking: LTR Ensemble
        from .services.ranking_ltr import RankingEnsemble
        ranker = RankingEnsemble()
        ranked_results = ranker.rank_candidates(results, parsed_query)
        
        # 3.5. Family-Based Result Filtering
        family = active_params.get('family', 1)
        
        if family == 6:  # Recommendation/Shortlist
            # Extract top N from query ("top 3", "best 5", etc.)
            top_n = self._extract_top_n(query)
            if top_n:
                ranked_results = ranked_results[:top_n]
            else:
                ranked_results = ranked_results[:5]  # Default to top 5

        # 4. Enhance: Add Badges & Market Snapshot
        # ... existing logic ...
        market_snapshot = {
            "total_count": len(ranked_results),
            "avg_price_global": sum(s['avg_price'] for s in ranked_results) / len(ranked_results) if ranked_results else 0,
            "top_country": ranked_results[0]['country'] if ranked_results else "N/A"
        }

        return Response({
            "query": query,
            "parsed_query": parsed_query, # Debug info
            "matched_subcategories": matched_subcategories,
            "results": ranked_results,
            "market_snapshot": market_snapshot,
            "count": len(ranked_results)
        })

    @action(detail=False, methods=['get'], url_path='supplier-detail')
    def supplier_detail(self, request):
        """
        GET /api/search/supplier-detail/?name=XYZ&query=dextrose
        Returns deep-dive data for the supplier page.
        """
        seller_name = request.query_params.get('name')
        query = request.query_params.get('query') # Context mainly to map to subcategories
        
        if not seller_name or not query:
            return Response({"error": "Params 'name' and 'query' are required"}, status=400)

        # 1. Re-match query to get context (subcategory IDs)
        # In a real app, we might pass subcategory_id directly from frontend to save NLP step
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(query)
        subcategory_ids = [m['id'] for m in matched_subcategories]
        
        # 2. Get Detail Stats
        aggregator = SupplierAggregator()
        details = aggregator.get_supplier_details(seller_name, subcategory_ids)
        
        if not details:
            return Response({"error": "Supplier not found for this product"}, status=404)
            
        # 3. Get Comparables
        # We need to fetch 'all suppliers' for this product to find comparables
        # Optimization: We could cache this or have a specialized query
        all_suppliers = aggregator.get_suppliers_for_subcategories(subcategory_ids)
        
        # Rank them using LTR so comparables are high quality
        from .services.ranking_ltr import RankingEnsemble
        ranker = RankingEnsemble()
        # Parse query might be minimal here, construct dummy if needed or pass context
        # If 'query' param exists, parse it.
        from .services.query_parser import QueryInterpreter
        context_query = QueryInterpreter().parse(query) if query else {}
        
        ranked_all = ranker.rank_candidates(all_suppliers, context_query)
        
        finder = ComparableFinder()
        comparables = finder.find_comparables(seller_name, subcategory_ids, ranked_all)
        

        # 4. Market Context (Dynamic)
        market_context = {
            "sentiment": "Neutral",
            "price_trend": "Stable"
        }
        
        if details['sparkline'] and len(details['sparkline']) >= 2:
            first = details['sparkline'][0]['price']
            last = details['sparkline'][-1]['price']
            
            if first > 0:
                change = (last - first) / first
                if change > 0.05:
                    market_context['price_trend'] = "Uptrend"
                    market_context['sentiment'] = "Bullish"
                elif change < -0.05:
                    market_context['price_trend'] = "Downtrend"
                    market_context['sentiment'] = "Bearish"

        return Response({
            "supplier": details,
            "comparables": comparables,
            "market_context": market_context
        })

    @action(detail=False, methods=['get'])
    def debug_nlp(self, request):
        """
        GET /api/search/query/debug_nlp/?q="term"
        Debug endpoint to see raw NLP matches without aggregation.
        """
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)
            
        matcher = QueryMatcher()
        matches = matcher.match(query)
        
        return Response({
            "query": query,
            "raw_matches": matches
        })
    
    def _extract_top_n(self, query):
        """
        Extract the number N from queries like 'top 3', 'best 5', 'suggest 10', etc.
        Returns the number or None if not found.
        """
        import re
        # Match patterns like "top 3", "best 5", "first 10", etc.
        pattern = r'\b(?:top|best|first|suggest)\s+(\d+)\b'
        match = re.search(pattern, query.lower())
        if match:
            return int(match.group(1))
        return None
    
    def _parse_time_range(self, time_range_str):
        """
        Parses strings like "Q1 2025", "2024", "Last 6 Months".
        Returns dict {start_date, end_date} or None.
        """
        import datetime
        
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
        elif "q2" in tr and "2025" in tr:
            start_date = datetime.date(2025, 4, 1)
            end_date = datetime.date(2025, 6, 30)
        elif "q3" in tr and "2025" in tr:
            start_date = datetime.date(2025, 7, 1)
            end_date = datetime.date(2025, 9, 30)
        elif "q4" in tr and "2025" in tr:
            start_date = datetime.date(2025, 10, 1)
            end_date = datetime.date(2025, 12, 31)
        elif "2025" in tr:
            start_date = datetime.date(2025, 1, 1)
            end_date = datetime.date(2025, 12, 31)
        elif "2024" in tr:
            start_date = datetime.date(2024, 1, 1)
            end_date = datetime.date(2024, 12, 31)
        elif "last 6 months" in tr or "last 6 month" in tr:
            end_date = today
            start_date = today - datetime.timedelta(days=180)
        elif "last 3 months" in tr or "last 3 month" in tr:
            end_date = today
            start_date = today - datetime.timedelta(days=90)
        elif "this year" in tr:
            start_date = datetime.date(today.year, 1, 1)
            end_date = datetime.date(today.year, 12, 31)
            
        if start_date or end_date:
            return {"start_date": start_date, "end_date": end_date}
            
        return None
