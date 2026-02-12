
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

class SearchViewSet(viewsets.ViewSet):
    """
    Unified Search API
    """
    permission_classes = [AllowAny] # Kept as it was not explicitly removed by the instruction

    def list(self, request):
        """
        GET /api/search/query/?q=...
        """
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=400)

        # Extract Filters
        subcategory_id_filter = request.query_params.get('subcategory_id')
        country_filter = request.query_params.get('country')
        # sort_by = request.query_params.get('sort_by') # Todo

        # 1. NLP: Match query to subcategories
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(query)
        
        if not matched_subcategories:
            return Response({
                "query": query,
                "matched_subcategories": [],
                "results": [],
                "message": "No matching products found."
            })

        # 2. Aggregation: Get suppliers for these subcategories
        # If user selected a specific subcategory (Product Filter), use only that ID
        if subcategory_id_filter:
            try:
                subcategory_ids = [int(subcategory_id_filter)]
            except ValueError:
                subcategory_ids = [m['id'] for m in matched_subcategories]
        else:
            # Default: Aggregation of matched subcategories
            # Logic refinement: If we have a very high confidence match (e.g., exact name match), 
            # we should prioritize that and exclude lower-confidence semantic matches to avoid inflating numbers.
            # E.g. "dextrose anhydrous" (1.0) vs "dextrose monohydrate" (0.78).
            
            top_match = matched_subcategories[0]
            if top_match['score'] > 0.95:
                # specific query detected. Filter out significantly lower scores.
                # Keep matches that are within 0.05 of the top score (handle synonyms / tight variants)
                threshold = top_match['score'] - 0.05
                subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
            else:
                # Vague query (e.g. "dextrose" might match "Anhydrous" and "Monohydrate" both at ~0.8 or 1.0 depending on naming)
                # If "dextrose" matches "Dextrose" (1.0), "Dextrose Anhydrous" (0.9), "Dextrose Mono" (0.9)
                # The user said for vague queries show ALL. 
                # But here "Dextrose" (generic) is actually a category. 
                # If query is "dextrose", and we have "Dextrose" category, we might just show that?
                # User requirement: "For a vague query ... show all relevant subcategories".
                # So if top match is NOT > 0.95 (or if it is generic), we keep all 'relevant' ones.
                # But wait, "Dextrose" category exists. 
                # Let's stick to the user's specific complaint: "dextrose anhydrous" (Specific) showed broader results.
                # So the logic 'if top > 0.95 truncate' works for the specific case.
                # For "dextrose", if "Dextrose" category is 1.0, it would truncate. 
                # But "Dextrose" category might NOT contain all dextrose transactions (data quality issues?).
                # Safe bet: Only strict filter if the query implies specificity (multi-word?).
                # Let's try the Score Threshold strategy first.
                
                # However, if the user explicitly wants "all relevant", we should be careful.
                # But "dextrose anhydrous" finding "monohydrate" is definitely wrong for a trader.
                subcategory_ids = [m['id'] for m in matched_subcategories]
            
        aggregator = SupplierAggregator()
        suppliers = aggregator.get_suppliers_for_subcategories(subcategory_ids)

        # 2.5 Apply Other Filters (Country, Price, etc.)
        if country_filter:
            suppliers = [s for s in suppliers if s['country'] and s['country'].lower() == country_filter.lower()]

        # 3. Ranking: Sort suppliers by score
        ranker = SupplierRanker()
        ranked_suppliers = ranker.rank_suppliers(suppliers)

        # 4. Enhance: Add Badges & Market Snapshot (Placeholder logic)
        for i, s in enumerate(ranked_suppliers):
            s['badges'] = []
            if i == 0:
                s['badges'].append("Top Ranked")
            if s['total_volume'] > 1000: # Arbitrary threshold
                s['badges'].append("High Volume")
                
        market_snapshot = {
            "total_suppliers": len(ranked_suppliers),
            "avg_price_global": sum(s['avg_price'] for s in ranked_suppliers) / len(ranked_suppliers) if ranked_suppliers else 0,
            "top_country": ranked_suppliers[0]['country'] if ranked_suppliers else "N/A"
        }

        return Response({
            "query": query,
            "matched_subcategories": matched_subcategories,
            "results": ranked_suppliers,
            "market_snapshot": market_snapshot,
            "count": len(ranked_suppliers)
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
        ranker = SupplierRanker()
        ranked_all = ranker.rank_suppliers(all_suppliers)
        
        finder = ComparableFinder()
        comparables = finder.find_comparables(seller_name, subcategory_ids, ranked_all)
        
        return Response({
            "supplier": details,
            "comparables": comparables,
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
