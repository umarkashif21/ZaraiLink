
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
            # F9: Hybrid / Multi-Intent — run each sub-intent through its own module
            # and return stacked sections. Return early before the single-intent pipeline.
            sections = []
            for sub in parsed_query['sub_intents']:
                section = self._run_sub_intent(sub, query)
                if section:
                    sections.append(section)
            return Response({
                "query": query,
                "parsed_query": parsed_query,
                "type": "multi_intent",
                "family": 9,
                "sections": sections,
                "results": [],
                "count": len(sections),
            })
        else:
            product_term = active_params.get('product') or ''
            # For F8 (buyer evidence) with a named buyer but no explicit product,
            # do NOT fall back to the raw query string. The raw query contains buyer
            # name / evidence keywords — feeding it to the NLP matcher produces false
            # subcategory matches that then incorrectly filter EvidenceRetriever's
            # queryset to zero transactions.
            f8_no_product = (
                active_params.get('family') == 8
                and bool(active_params.get('counterparty_name'))
                and not product_term
            )
            nlp_search_term = '' if f8_no_product else (product_term or query)
        
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
        # For filter-only queries (empty product but has filters), skip NLP
        has_filters = bool(country_filter or price_filter or volume_req)
        matched_subcategories = []
        subcategory_ids = None  # None = all products
        
        if nlp_search_term and nlp_search_term.strip():
            matcher = QueryMatcher()
            matched_subcategories = matcher.match(nlp_search_term)
        
        # F8 with a named buyer is valid even without a product match —
        # the user wants that buyer's transaction history regardless of product.
        is_f8_with_buyer = (
            active_params.get('family') == 8
            and bool(active_params.get('counterparty_name'))
        )
        if not matched_subcategories and not has_filters and not is_f8_with_buyer:
            # No product match AND no filters — truly empty query
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
                subcategory_ids = [m['id'] for m in matched_subcategories] if matched_subcategories else None
        elif matched_subcategories:
            # Default aggregation logic
            top_match = matched_subcategories[0]
            if top_match['score'] > 0.95:
                threshold = top_match['score'] - 0.05
                subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
            else:
                subcategory_ids = [m['id'] for m in matched_subcategories]
        # else: subcategory_ids stays None — filter-only query, search all products

        # 1.5 Variant / ProductItem Logic
        product_item_filter = None
        
        # A. Explicit Filter from Sidebar (Query Param)
        # Supports ?product_item=123
        req_item_id = request.query_params.get('product_item')
        if req_item_id:
            try:
                product_item_filter = [int(req_item_id)]
            except ValueError:
                pass
                
        # B. Auto-Filter from NLP (Specific Search)
        # If user searched "Dextrose Anhydrous", we might have multiple matches (dupes).
        # We must collect matched variants from ALL subcategories that matched.
        if not product_item_filter and matched_subcategories:
             auto_variants = []
             # Collect from all subcategories we are about to search
             # (i.e. those that made it into subcategory_ids)
             target_subcat_ids = set(subcategory_ids) if subcategory_ids else set()
             
             for match in matched_subcategories:
                 if match['id'] in target_subcat_ids and match.get('matched_variants'):
                     auto_variants.extend(match['matched_variants'])
            
             if auto_variants:
                 product_item_filter = list(set(auto_variants)) # Unique IDs

        # 3. Family-Based Routing — determine family before aggregation
        family = active_params.get('family', 1)

        # C. Fetch Available Variants for Sidebar (not needed for Family 7)
        available_variants = []
        if family != 7 and subcategory_ids:
            from trade_data.models import ProductItem
            items = ProductItem.objects.filter(sub_category_id__in=subcategory_ids).values('id', 'name', 'sub_category_id')
            available_variants = list(items)

        # Family 7: go straight to CountryComparator, skip aggregator + ranker entirely
        if family == 7:
            from .services.aggregation import CountryComparator
            comparator = CountryComparator()
            cc_result = comparator.compare_countries(
                subcategory_ids,
                intent=intent,
                country_filter=country_filter if country_filter else None,
                time_filter=time_filter,
                product_item_filter=product_item_filter,
            )
            country_data = cc_result['results']
            country_warnings = cc_result['warnings']
            country_data_context = cc_result['data_context']

            f7_market_snapshot = None
            if country_data:
                f7_market_snapshot = {
                    "total_count": len(country_data),
                    "avg_price_global": sum(c['avg_price'] for c in country_data) / len(country_data),
                    "top_country": country_data[0]['country'],
                }

            return Response({
                "query": query,
                "parsed_query": parsed_query,
                "matched_subcategories": matched_subcategories,
                "family": 7,
                "type": "country_comparison",
                "country_comparison": country_data,
                "country_warnings": country_warnings,
                "data_context": country_data_context,
                "market_snapshot": f7_market_snapshot,
                "results": [],
                "count": 0,
            })

        # Family 8: direct evidence retrieval — skip aggregator + ranker
        if family == 8:
            from .services.aggregation import EvidenceRetriever
            retriever = EvidenceRetriever()
            buyer_name = active_params.get('counterparty_name') or None
            # If no product was parsed, use None (no subcat filter) not an empty list
            f8_subcats = subcategory_ids if subcategory_ids else None
            evidence = retriever.get_transaction_evidence(
                subcategory_ids=f8_subcats,
                buyer_name=buyer_name,
                country_filter=country_filter if country_filter else None,
                time_filter=time_filter,
            )
            return Response({
                "query": query,
                "parsed_query": parsed_query,
                "matched_subcategories": matched_subcategories,
                "family": 8,
                "type": "transaction_evidence",
                "transactions": evidence['transactions'],
                "buyer_summary": evidence['buyer_summary'],
                "buyer_found": evidence['buyer_found'],
                "similar_buyers": evidence['similar_buyers'],
                "total_shown": evidence['total_shown'],
                "results": [],
                "count": 0,
            })

        aggregator = SupplierAggregator()
        results = aggregator.get_suppliers_for_subcategories(
            subcategory_ids,
            intent=intent,
            scope=active_params.get('scope', 'WORLDWIDE'),
            country_filter=country_filter,
            price_filter=price_filter,
            volume_filter=volume_req,
            time_filter=time_filter,
            product_item_filter=product_item_filter
        )

        from .services.ranking_ltr import RankingEnsemble
        ranker = RankingEnsemble()
        ranked_results = ranker.rank_candidates(results, parsed_query)

        if family == 6:  # Recommendation/Shortlist
            top_n = self._extract_top_n(query)
            if top_n:
                ranked_results = ranked_results[:top_n]
            else:
                ranked_results = ranked_results[:5]

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
            "available_variants": available_variants, # For Sidebar
            "active_variant": product_item_filter[0] if product_item_filter else None,
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
        # Use Interpreter to extract "dextrose" from "Import dextrose from China..."
        interpreter = QueryInterpreter()
        parsed_query = interpreter.parse(query)
        nlp_search_term = parsed_query.get('product') or query

        matcher = QueryMatcher()
        matched_subcategories = matcher.match(nlp_search_term)
        subcategory_ids = [m['id'] for m in matched_subcategories]
        
        # 2. Get Detail Stats
        # 2. Get Detail Stats based on Intent
        intent = parsed_query.get('intent', 'BUY')
        aggregator = SupplierAggregator()
        
        if intent == 'SELL':
            # User is selling, so we are looking for a BUYER
            details = aggregator.get_buyer_details(seller_name, subcategory_ids)
        else:
            # User is buying, so we are looking for a SUPPLIER
            details = aggregator.get_supplier_details(seller_name, subcategory_ids)
        
        if not details:
            return Response({"error": f"{'Buyer' if intent == 'SELL' else 'Supplier'} not found for this product"}, status=404)
            
        # 3. Get Comparables
        # Fetch appropriate candidates (Buyers or Suppliers)
        all_candidates = aggregator.get_suppliers_for_subcategories(subcategory_ids, intent=intent)
        
        # Rank them using LTR
        from .services.ranking_ltr import RankingEnsemble
        ranker = RankingEnsemble()
        context_query = parsed_query if parsed_query else {}
        
        ranked_candidates = ranker.rank_candidates(all_candidates, context_query)
        
        finder = ComparableFinder()
        comparables = finder.find_comparables(seller_name, subcategory_ids, ranked_candidates)
        
        # 4. Market Context (Dynamic)
        market_context = {
            "sentiment": "Neutral",
            "price_trend": "Stable"
        }
        
        if details['sparkline'] and len(details['sparkline']) >= 2:
            first = details['sparkline'][0]['price']
            last = details['sparkline'][-1]['price']
            
            # For Buyers, high price is good? Or bad?
            # Typically price trend is market price.
            if first > 0:
                change = (last - first) / first
                if change > 0.05:
                    market_context['price_trend'] = "Uptrend"
                    market_context['sentiment'] = "Bullish"
                elif change < -0.05:
                    market_context['price_trend'] = "Downtrend"
                    market_context['sentiment'] = "Bearish"

        return Response({
            "supplier": details, # Frontend expects 'supplier' key for now, we can rename or keep it
            "comparables": comparables,
            "market_context": market_context,
            "type": "BUYER" if intent == 'SELL' else "SUPPLIER"
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

    def _run_sub_intent(self, sub_params, raw_query):
        """
        Run a single parsed sub-intent through its appropriate family module.
        Returns a section dict for inclusion in a Family 9 multi-intent response,
        or None if the sub-intent produces no usable output.
        """
        from .services.nlp import QueryMatcher
        from .services.aggregation import SupplierAggregator, CountryComparator
        from .services.ranking_ltr import RankingEnsemble

        family = sub_params.get('family', 1)
        product = sub_params.get('product') or ''
        country_filter = sub_params.get('country_filter', [])
        volume_req = sub_params.get('volume_mt')
        time_range_str = sub_params.get('time_range')
        intent = sub_params.get('intent', 'BUY')

        price_filter = {}
        if sub_params.get('price_ceiling'):
            price_filter['ceiling'] = sub_params['price_ceiling']
        if sub_params.get('price_floor'):
            price_filter['floor'] = sub_params['price_floor']

        time_filter = self._parse_time_range(time_range_str) if time_range_str else None

        # NLP → subcategory IDs (only when a product term exists)
        matched_subcategories = []
        subcategory_ids = None
        if product:
            matcher = QueryMatcher()
            matched_subcategories = matcher.match(product)
            if matched_subcategories:
                top_match = matched_subcategories[0]
                if top_match['score'] > 0.95:
                    threshold = top_match['score'] - 0.05
                    subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
                else:
                    subcategory_ids = [m['id'] for m in matched_subcategories]

        SECTION_META = {
            1: ("Buyer Discovery",        "Who buys this product?"),
            2: ("Country-Filtered Buyers","Buyers in specific countries"),
            3: ("Volume-Matched Buyers",  "Buyers matching your order size"),
            4: ("Price-Filtered Buyers",  "Buyers at your target price"),
            5: ("Active Recent Buyers",   "Buyers who purchased recently"),
            6: ("Top Recommendations",    "Best buyers to approach first"),
            7: ("Country Comparison",     "Which countries have the most demand?"),
        }
        label, intent_answered = SECTION_META.get(family, ("Results", "Query results"))

        # Family 7 → CountryComparator
        if family == 7:
            comparator = CountryComparator()
            cc_result = comparator.compare_countries(
                subcategory_ids,
                intent=intent,
                country_filter=country_filter if country_filter else None,
                time_filter=time_filter,
            )
            return {
                "label": label,
                "family": 7,
                "intent_answered": intent_answered,
                "country_comparison": cc_result['results'],
                "country_warnings": cc_result['warnings'],
                "data_context": cc_result['data_context'],
            }

        # Families 1–6 → SupplierAggregator + RankingEnsemble
        aggregator = SupplierAggregator()
        results = aggregator.get_suppliers_for_subcategories(
            subcategory_ids,
            intent=intent,
            scope=sub_params.get('scope', 'WORLDWIDE'),
            country_filter=country_filter,
            price_filter=price_filter,
            volume_filter=volume_req,
            time_filter=time_filter,
        )
        ranker = RankingEnsemble()
        ranked_results = ranker.rank_candidates(results, sub_params)

        if family == 6:
            top_n = self._extract_top_n(raw_query) or 5
            ranked_results = ranked_results[:top_n]

        return {
            "label": label,
            "family": family,
            "intent_answered": intent_answered,
            "results": ranked_results,
            "matched_subcategories": matched_subcategories,
        }
