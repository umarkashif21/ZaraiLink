import re
import datetime

from django.db.models import Q
from django.db.models.functions import Lower
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .services.nlp import QueryMatcher
from .services.aggregation import SupplierAggregator
from .services.ranking import ComparableFinder
from .services.ranking_ltr import RankingEnsemble
from .services.query_parser import QueryInterpreter
from trade_data.models import Transaction

# Module-level singleton to avoid reloading LTR model per request
_ranking_ensemble = None

def get_ranking_ensemble():
    global _ranking_ensemble
    if _ranking_ensemble is None:
        _ranking_ensemble = RankingEnsemble()
    return _ranking_ensemble

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
        active_scope = active_params.get('scope', 'WORLDWIDE')

        # BUG-024: If user says "buy from Pakistan" with WORLDWIDE scope,
        # auto-switch to PAKISTAN scope since WORLDWIDE filters by origin_country
        # and Pakistan's imports have foreign origins.
        if active_scope == 'WORLDWIDE' and country_filter:
            pakistan_in_filter = [c for c in country_filter if c.lower() == 'pakistan']
            if pakistan_in_filter and len(country_filter) == 1:
                active_scope = 'PAKISTAN'
                active_params['scope'] = 'PAKISTAN'
                country_filter = []
                active_params['country_filter'] = []

        # BUG-007: Check for both BUY and SELL intent conflicts
        if active_scope == 'PAKISTAN' and country_filter:
            non_pakistan_countries = [c for c in country_filter if c.lower() != 'pakistan']
            if non_pakistan_countries:
                if intent == 'BUY':
                    conflict_msg = f"You are searching for Pakistani suppliers but specified {', '.join(non_pakistan_countries)} as a country filter. Switch scope to Worldwide to search international suppliers."
                else:
                    conflict_msg = f"You are searching for Pakistani buyers but specified {', '.join(non_pakistan_countries)} as a country filter. Switch scope to Worldwide to search international buyers."
                return Response({
                    "query": query,
                    "parsed_query": parsed_query,
                    "error": "scope_country_conflict",
                    "message": conflict_msg,
                    "results": [],
                    "count": 0
                })

        # 1. NLP: Match query to subcategories
        # Only run NLP if we have a real product term (not empty after stopword removal)
        product_text = active_params.get('product', '').strip()
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(nlp_search_term) if product_text else []

        # Fallback strategies when NLP finds no product match
        company_name_search = False
        browse_all_search = False

        if not matched_subcategories:
            # Strategy A: Try the raw query as a company/counterparty name search
            company_results = self._search_by_company_name(query, intent, active_params.get('scope', 'WORLDWIDE'))
            if company_results:
                company_name_search = True
                results = company_results
            else:
                # Strategy B: Intent-only query ("buyers", "find suppliers") — browse all products
                product_text = active_params.get('product', '').strip()
                if not product_text:
                    browse_all_search = True
                    all_subcategory_ids = list(
                        Transaction.objects.values_list('product_item__sub_category_id', flat=True)
                        .distinct()[:50]
                    )
                    if all_subcategory_ids:
                        aggregator = SupplierAggregator()
                        browse_scope = active_params.get('scope', 'WORLDWIDE')
                        results = aggregator.get_suppliers_for_subcategories(
                            all_subcategory_ids,
                            intent=intent,
                            scope=browse_scope,
                            country_filter=country_filter,
                            price_filter=price_filter,
                            volume_filter=volume_req,
                            time_filter=time_filter
                        )
                        # If no results (e.g., SELL+WORLDWIDE with no EXPORT data),
                        # try SELL+PAKISTAN as fallback (Pakistani buyers)
                        if not results and intent == 'SELL' and browse_scope == 'WORLDWIDE':
                            results = aggregator.get_suppliers_for_subcategories(
                                all_subcategory_ids,
                                intent='SELL',
                                scope='PAKISTAN',
                                country_filter=country_filter,
                            )
                        # Similarly for BUY+PAKISTAN with no EXPORT data
                        if not results and intent == 'BUY' and browse_scope == 'PAKISTAN':
                            results = aggregator.get_suppliers_for_subcategories(
                                all_subcategory_ids,
                                intent='BUY',
                                scope='WORLDWIDE',
                                country_filter=country_filter,
                            )
                    else:
                        results = []
                else:
                    return Response({
                        "query": query,
                        "parsed_query": parsed_query,
                        "matched_subcategories": [],
                        "results": [],
                        "message": f"No matching products found for \"{nlp_search_term}\". Try searching for a product name like 'dextrose', 'sugar', or 'urea'."
                    })

        if not company_name_search and not browse_all_search:
            # Normal product-based search path
            # 2. Aggregation: Get suppliers/buyers
            if subcategory_id_filter:
                try:
                    subcategory_ids = [int(subcategory_id_filter)]
                except ValueError:
                    subcategory_ids = [m['id'] for m in matched_subcategories]
            else:
                top_match = matched_subcategories[0]
                if top_match['score'] > 0.95:
                    threshold = top_match['score'] - 0.05
                    subcategory_ids = [m['id'] for m in matched_subcategories if m['score'] >= threshold]
                else:
                    subcategory_ids = [m['id'] for m in matched_subcategories]

            aggregator = SupplierAggregator()
            results = aggregator.get_suppliers_for_subcategories(
                subcategory_ids,
                intent=intent,
                scope=active_params.get('scope', 'WORLDWIDE'),
                country_filter=country_filter,
                price_filter=price_filter,
                volume_filter=volume_req,
                time_filter=time_filter
            )

            # BUG-022: Filter by counterparty name if extracted
            counterparty = active_params.get('counterparty_name')
            if counterparty and results:
                filtered = [r for r in results if counterparty.lower() in r.get('name', '').lower()]
                if filtered:
                    results = filtered

        # 3. Ranking: LTR Ensemble
        # Enrich candidates with volume_fit before ranking
        for cand in results:
            if volume_req:
                max_vol = cand.get('max_shipment_vol', 0)
                total_vol = cand.get('total_volume', 0)
                if max_vol >= volume_req * 1.2:
                    cand['volume_fit'] = 'Strong'
                elif max_vol >= volume_req:
                    cand['volume_fit'] = 'Good'
                elif total_vol >= volume_req:
                    cand['volume_fit'] = 'Partial'
                else:
                    cand['volume_fit'] = 'Low'

        ranker = get_ranking_ensemble()
        ranked_results = ranker.rank_candidates(results, active_params)
        
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
        priced_results = [s for s in ranked_results if s.get('avg_price') is not None]
        market_snapshot = {
            "total_count": len(ranked_results),
            "avg_price_global": sum(s['avg_price'] for s in priced_results) / len(priced_results) if priced_results else None,
            "top_country": ranked_results[0]['country'] if ranked_results else "N/A"
        }

        response_data = {
            "query": query,
            "parsed_query": parsed_query,
            "matched_subcategories": matched_subcategories,
            "results": ranked_results,
            "market_snapshot": market_snapshot,
            "count": len(ranked_results)
        }
        if company_name_search:
            response_data["search_type"] = "company"
            response_data["message"] = f"Showing results for company matching \"{query}\""
        elif browse_all_search:
            response_data["search_type"] = "browse"
            entity_type = "buyers" if intent == "SELL" else "suppliers"
            response_data["message"] = f"Browsing all {entity_type}"

        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='supplier-detail')
    def supplier_detail(self, request):
        """
        GET /api/search/supplier-detail/?name=XYZ&query=dextrose&intent=BUY&scope=WORLDWIDE
        Returns deep-dive data for the supplier/buyer page.
        """
        name = request.query_params.get('name')
        query = request.query_params.get('query')
        detail_intent = request.query_params.get('intent', 'BUY').upper()
        detail_scope = request.query_params.get('scope', 'WORLDWIDE').upper()

        if not name or not query:
            return Response({"error": "Params 'name' and 'query' are required"}, status=400)

        # 1. Parse query to extract just the product term
        interpreter = QueryInterpreter()
        parsed = interpreter.parse(query)
        search_term = parsed.get('product') or query

        # 2. Match to subcategories using the cleaned product term
        matcher = QueryMatcher()
        matched_subcategories = matcher.match(search_term)
        subcategory_ids = [m['id'] for m in matched_subcategories]

        # 3. Get Detail Stats (pass intent so correct field is used)
        aggregator = SupplierAggregator()
        details = aggregator.get_supplier_details(name, subcategory_ids, intent=detail_intent)

        if not details:
            return Response({"error": "Supplier/buyer not found for this product"}, status=404)

        # 4. Get Comparables using same intent and scope as original search
        all_suppliers = aggregator.get_suppliers_for_subcategories(
            subcategory_ids, intent=detail_intent, scope=detail_scope
        )

        ranker = get_ranking_ensemble()
        context_query = parsed if parsed else {}
        ranked_all = ranker.rank_candidates(all_suppliers, context_query)

        finder = ComparableFinder()
        comparables = finder.find_comparables(name, subcategory_ids, ranked_all)
        

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
    
    def _search_by_company_name(self, query, intent='BUY', scope='WORLDWIDE'):
        """
        Search for companies by name across all products.
        Returns aggregated results matching the company name, or empty list.
        """
        search_term = query.strip()
        # Remove common intent words to isolate the company name
        for word in ['buy', 'sell', 'find', 'search', 'show', 'from', 'suppliers', 'buyers']:
            search_term = re.sub(r'\b' + word + r'\b', '', search_term, flags=re.IGNORECASE)
        search_term = search_term.strip()
        if not search_term or len(search_term) < 2:
            return []

        # Determine which field to search based on intent
        if intent == 'SELL':
            if scope == 'PAKISTAN':
                name_field = 'buyer'
                qs = Transaction.objects.filter(trade_type='IMPORT', destination_country='Pakistan')
            else:
                name_field = 'buyer'
                qs = Transaction.objects.filter(trade_type='EXPORT', origin_country='Pakistan')
        else:
            if scope == 'PAKISTAN':
                name_field = 'seller'
                qs = Transaction.objects.filter(trade_type='EXPORT', origin_country='Pakistan')
            else:
                name_field = 'seller'
                qs = Transaction.objects.filter(trade_type='IMPORT', destination_country='Pakistan')

        # Case-insensitive partial match on company name
        filter_kwargs = {f"{name_field}__icontains": search_term}
        matched_qs = qs.filter(**filter_kwargs)

        # If exact partial match fails, try fuzzy: search each word individually
        if not matched_qs.exists():
            words = search_term.split()
            q_filter = Q()
            for word in words:
                if len(word) >= 3:
                    q_filter &= Q(**{f"{name_field}__icontains": word})
            if q_filter:
                matched_qs = qs.filter(q_filter)

        # If still no match, try progressively shorter prefixes of the longest word
        if not matched_qs.exists():
            words = sorted(search_term.split(), key=len, reverse=True)
            for word in words:
                if len(word) >= 4:
                    # Try shrinking prefix: "seawell" → "seawel" → "seawe" → "seaw"
                    for trim in range(1, len(word) - 2):
                        prefix = word[:len(word)-trim]
                        if len(prefix) < 3:
                            break
                        matched_qs = qs.filter(**{f"{name_field}__icontains": prefix})
                        if matched_qs.exists():
                            break
                    if matched_qs.exists():
                        break

        if not matched_qs.exists():
            return []

        qs = matched_qs

        # Aggregate results for matching companies
        from django.db.models import Sum, Count, Avg, Max
        country_field = 'origin_country' if name_field == 'seller' else 'destination_country'

        results = qs.values(name_field, country_field).annotate(
            total_volume=Sum('qty_mt'),
            avg_price=Avg('usd_per_mt'),
            shipment_count=Count('id'),
            last_shipment_date=Max('reporting_date'),
            max_shipment_vol=Max('qty_mt')
        ).order_by('-total_volume')

        counterparties = []
        for r in results:
            counterparties.append({
                "name": r[name_field],
                "country": r[country_field],
                "total_volume": float(r['total_volume'] or 0),
                "avg_price": float(r['avg_price']) if r['avg_price'] is not None else None,
                "shipment_count": r['shipment_count'],
                "last_shipment_date": r['last_shipment_date'],
                "max_shipment_vol": float(r['max_shipment_vol'] or 0),
                "type": "Buyer" if intent == 'SELL' else "Supplier"
            })

        return counterparties

    def _extract_top_n(self, query):
        """
        Extract the number N from queries like 'top 3', 'best 5', 'suggest 10', etc.
        Returns the number or None if not found.
        """
        # Match patterns like "top 3", "best 5", "first 10", etc.
        pattern = r'\b(?:top|best|first|suggest)\s+(\d+)\b'
        match = re.search(pattern, query.lower())
        if match:
            return int(match.group(1))
        return None
    
    MONTH_MAP = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }

    def _parse_time_range(self, time_range_str):
        """
        Parses strings like "Q1 2025", "2024", "Last 6 Months", "last 2 years",
        "january to march", "this year".
        Returns dict {start_date, end_date} or None.
        """
        if not time_range_str:
            return None

        today = datetime.date.today()
        start_date = None
        end_date = None
        tr = time_range_str.lower().strip()

        # 1. Dynamic quarter parsing: "Q1 2025", "Q3 2023", "Q2" (defaults to current year)
        q_match = re.search(r'\bq([1-4])\s*(\d{4})?\b', tr)
        if q_match:
            quarter = int(q_match.group(1))
            year = int(q_match.group(2)) if q_match.group(2) else today.year
            q_starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
            q_ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
            start_date = datetime.date(year, *q_starts[quarter])
            end_date = datetime.date(year, *q_ends[quarter])

        # 2. "last N months/years" — dynamic
        elif re.search(r'last\s+\d+\s+(?:month|year)', tr):
            m = re.search(r'last\s+(\d+)\s+(month|year)s?', tr)
            if m:
                n = int(m.group(1))
                unit = m.group(2)
                end_date = today
                if unit == 'month':
                    start_date = today - datetime.timedelta(days=n * 30)
                else:
                    start_date = today - datetime.timedelta(days=n * 365)

        # 3. Month-name range: "january to march"
        elif ' to ' in tr:
            parts = tr.split(' to ')
            if len(parts) == 2:
                m1 = self.MONTH_MAP.get(parts[0].strip())
                m2 = self.MONTH_MAP.get(parts[1].strip())
                if m1 and m2:
                    import calendar
                    year = today.year
                    start_date = datetime.date(year, m1, 1)
                    last_day = calendar.monthrange(year, m2)[1]
                    end_date = datetime.date(year, m2, last_day)

        # 4. "this year"
        elif "this year" in tr:
            start_date = datetime.date(today.year, 1, 1)
            end_date = datetime.date(today.year, 12, 31)

        # 5. Plain year: "2024", "2025"
        else:
            year_match = re.search(r'\b(20\d{2})\b', tr)
            if year_match:
                year = int(year_match.group(1))
                start_date = datetime.date(year, 1, 1)
                end_date = datetime.date(year, 12, 31)

        if start_date or end_date:
            return {"start_date": start_date, "end_date": end_date}

        return None
